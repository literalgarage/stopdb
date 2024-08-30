from mimetypes import guess_type

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField

from .fields import PartialDateField


class RegionManager(models.Manager):
    def _group_name(self, name: str) -> str:
        return f"{name} Admins"

    def create_with_group(self, name: str) -> "Region":
        """Create a region with a group."""
        slug = slugify(name)
        group = Group.objects.create(name=self._group_name(name))
        return self.create(name=name, slug=slug, group=group)

    def get_or_create_with_group(self, name: str) -> tuple["Region", bool]:
        """Get or create a region with a group."""
        slug = slugify(name)
        group, _ = Group.objects.get_or_create(name=self._group_name(name))
        return self.get_or_create(slug=slug, defaults={"name": name, "group": group})


class Region(models.Model):
    """A geographic region of incidents under common administration."""

    objects: RegionManager = RegionManager()

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="region",
        help_text="The group that controls this region",
    )

    def __str__(self) -> str:
        return f"Region ({self.pk}): {self.name}"


class Attachment(models.Model):
    """An arbitrary file attachment."""

    name = models.CharField(max_length=100, help_text="Includes file extension")
    data = models.BinaryField()

    # Type hints for reverse relations
    extras: models.QuerySet["Extra"]
    logos_of_districts: models.QuerySet["SchoolDistrict"]
    school_response_materials: models.QuerySet["Incident"]
    supporting_materials: models.QuerySet["Incident"]

    @property
    def content_type(self) -> str | None:
        return guess_type(self.name)[0]

    def __str__(self) -> str:
        return f"Attachment ({self.pk}): {self.name}"


class Extra(models.Model):
    """Arbitrary extra data associated with a model."""

    name = models.CharField(max_length=100)
    value = models.TextField()
    attachment = models.ForeignKey(
        Attachment,
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="extras",
    )

    def __str__(self) -> str:
        return f"Extra ({self.pk}): {self.name} -> {self.value}"


class Link(models.Model):
    """An external link."""

    name = models.CharField(max_length=100, blank=True, default="")
    url = models.URLField()

    def __str__(self) -> str:
        return f"Link ({self.pk}): {self.name}"


class SchoolDistrict(models.Model):
    """A school district."""

    name = models.CharField(max_length=100)
    logo = models.ForeignKey(
        Attachment,
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logos_of_districts",
    )
    url = models.URLField(blank=True)
    twitter = models.URLField(blank=True, default="")
    facebook = models.URLField(blank=True, default="")
    phone = PhoneNumberField(blank=True, default="")

    superintendent_name = models.CharField(max_length=100)
    superintendent_email = models.EmailField(blank=True)

    civil_rights_url = models.URLField(blank=True)
    civil_rights_contact_name = models.CharField(max_length=100, blank=True)
    civil_rights_contact_email = models.EmailField(blank=True)

    hib_url = models.URLField(blank=True)
    hib_form_url = models.URLField(blank=True)
    hib_contact_name = models.CharField(max_length=100, blank=True)
    hib_contact_email = models.EmailField(blank=True)

    board_url = models.URLField(blank=True)

    extras = models.ManyToManyField(Extra, blank=True, related_name="district_extras")

    def __str__(self) -> str:
        return f"{self.name} ({self.pk})"


class School(models.Model):
    """A school."""

    name = models.CharField(max_length=100)
    url = models.URLField()
    district = models.ForeignKey(
        SchoolDistrict,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="schools",
    )
    street = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=5, blank=True)
    latitude = models.FloatField(null=True, blank=True, default=None)
    longitude = models.FloatField(null=True, blank=True, default=None)

    is_public = models.BooleanField()

    is_elementary = models.BooleanField()
    is_middle = models.BooleanField()
    is_high = models.BooleanField()

    extras = models.ManyToManyField(Extra, blank=True, related_name="school_extras")

    # Validate that at least one of the three is true
    def clean(self):
        if not (self.is_elementary or self.is_middle or self.is_high):
            raise ValidationError(
                "School must be at least one of elementary, middle, or high"
            )

    def __str__(self) -> str:
        return f"{self.name} ({self.pk})"


class IncidentType(models.Model):
    """A type of incident."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Incident type ({self.pk}): {self.name}"


class SourceType(models.Model):
    """A type of source for an incident."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Source type: {self.name} ({self.pk})"


class Incident(models.Model):
    """An incident."""

    region = models.ForeignKey(
        Region,
        blank=False,
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="The region that this incident belongs to",
    )

    description = models.TextField()
    notes = models.TextField(
        blank=True, default="", help_text="Administrative notes (never shown publicly)"
    )

    submitted_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(null=True, blank=True, default=None)

    @property
    def is_published(self) -> bool:
        return self.published_at is not None

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="publisher",
    )

    occurred_at = PartialDateField(help_text="When the incident occurred")

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="incidents"
    )
    incident_types = models.ManyToManyField(IncidentType)
    source_types = models.ManyToManyField(SourceType)

    related_links = models.ManyToManyField(Link, blank=True, related_name="incidents")
    supporting_materials = models.ManyToManyField(
        Attachment, blank=True, related_name="supporting_materials"
    )

    reported_to_school = models.BooleanField(default=False)
    reported_at = PartialDateField(blank=True, default="")

    school_responded = models.BooleanField(default=False)
    school_responded_at = PartialDateField(blank=True, default="")
    school_response = models.TextField(blank=True, default="")
    school_response_materials = models.ManyToManyField(
        Attachment, blank=True, related_name="school_response_materials"
    )

    extras = models.ManyToManyField(Extra)

    def __str__(self) -> str:
        return f"Incident ({self.pk}): {self.occurred_at} {self.school.name} {self.description[:333]}..."


def group_controlling_attachment(attachment: Attachment) -> Group | None:
    """
    Given an attachment, return the group that controls it, if any.
    We do this as follows:

    1. We check if the attachment is part of `supporting_materials` for
       any incident. If so, we return the group of the incident.
    2. We check if the attachment is part of `school_response_materials`
       for any incident. If so, we return the group of the incident.
    3. We check if the attachment is part of an `extras` for any incident.
       If so, we return the group of the incident.
    4. Otherwise, we return None.
    """

    # TODO DAVE: This is inefficient. We should use a reverse
    # relation on the Attachment model to get all incidents that
    # reference the attachment. This would require a ManyToManyField
    # from Attachment to Incident, which would be a good idea anyway
    # for other reasons.

    for incident in Incident.objects.all():
        if attachment in incident.supporting_materials.all():
            return incident.group
        if attachment in incident.school_response_materials.all():
            return incident.group
        if attachment in incident.extras.all():
            return incident.group

    return None
