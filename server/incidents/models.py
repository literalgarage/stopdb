from mimetypes import guess_type

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from phonenumber_field.modelfields import PhoneNumberField

from .fields import PartialDateField
from .kebab import pascal_to_kebab

# -----------------------------------------------------------------------------
# Abstract base models
# -----------------------------------------------------------------------------

# NOTE: Django supports a notion of a GenericForeignKey, which normally we
# would probably use for Attachment and for Extras. But because the
# SQL database we're creating is expected to be used by third parties without
# the convenience of Django's ORM, we're going to use a more explicit
# approach here.


class AttachmentBase(models.Model):
    """An arbitrary file attachment."""

    # NOTE WELL: keeping attachments in the database is not a good idea
    # over the long term, but boy is it convenient for now. Eventually
    # we should connect an S3 bucket and use Django Storages to store
    # attachments there.

    name = models.CharField(
        max_length=100, help_text="Includes file extension", unique=True
    )
    data = models.BinaryField()

    @property
    def content_type(self) -> str | None:
        return guess_type(self.name)[0]

    @property
    def is_image(self) -> bool:
        content_type = self.content_type
        if content_type is None:
            return False
        return content_type.startswith("image/") or content_type == "image/svg+xml"

    @property
    def url(self) -> str:
        kebab_name = pascal_to_kebab(str(self._meta))
        return reverse("incidents:attachment", args=[kebab_name, self.name])

    def __str__(self) -> str:
        return f"{str(self._meta)} ({self.pk}): {self.name}"

    class Meta:
        abstract = True


class ExtraBase(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    value = models.TextField()

    def __str__(self) -> str:
        return f"{str(self._meta)} ({self.pk}): {self.name} -> {self.value}"

    class Meta:
        abstract = True


# -----------------------------------------------------------------------------
# Concrete models: Region
# -----------------------------------------------------------------------------


class RegionManager(models.Manager):
    """Manages a table of geographic regions."""

    def _group_name(self, name: str) -> str:
        return f"{name} Admins"

    def create_with_group(self, name: str) -> "Region":
        """Create a region with a group."""
        slug = slugify(name)
        group = Group.objects.create(name=Region.default_group_name(name))
        return self.create(name=name, slug=slug, group=group)

    def get_or_create_with_group(self, name: str) -> tuple["Region", bool]:
        """Get or create a region with a group."""
        slug = slugify(name)
        group, _ = Group.objects.get_or_create(name=Region.default_group_name(name))
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

    @classmethod
    def default_group_name(cls, name: str) -> str:
        return f"{name} Admins"

    def __str__(self) -> str:
        return f"Region ({self.pk}): {self.name}"


# -----------------------------------------------------------------------------
# Concrete models: School District & School
# -----------------------------------------------------------------------------


class SchoolDistrict(models.Model):
    """A school district."""

    name = models.CharField(max_length=100)

    logo: "DistrictLogo"

    @property
    def safe_logo(self) -> "DistrictLogo | None":
        try:
            return self.logo
        except DistrictLogo.DoesNotExist:
            return None

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

    def __str__(self) -> str:
        return f"{self.name} ({self.pk})"


class DistrictLogo(AttachmentBase):
    """A logo for a school district."""

    district = models.OneToOneField(
        SchoolDistrict,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="logo",
    )

    class Meta:
        abstract = False


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

    # Validate that at least one of the three is true
    def clean(self):
        if not (self.is_elementary or self.is_middle or self.is_high):
            raise ValidationError(
                "School must be at least one of elementary, middle, or high"
            )

    def __str__(self) -> str:
        return f"{self.name} ({self.pk})"


# -----------------------------------------------------------------------------
# Concrete models: Incidents & related
# -----------------------------------------------------------------------------


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


class RelatedLink(models.Model):
    """An external link related to an incident."""

    name = models.CharField(max_length=100, blank=True, default="")
    url = models.URLField()
    incident = models.ForeignKey(
        "Incident", on_delete=models.CASCADE, related_name="related_links"
    )

    def __str__(self) -> str:
        return f"Link ({self.pk}): {self.name}"


class IncidentExtra(ExtraBase):
    """An extra field for an incident."""

    incident = models.ForeignKey(
        "Incident", on_delete=models.CASCADE, related_name="extras"
    )

    class Meta:
        abstract = False
        verbose_name = "Incident Extra"
        verbose_name_plural = "Incident Extras"


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

    # TODO DAVE: consider inbound reports vs published incidents
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

    supporting_materials: models.QuerySet["SupportingMaterial"]
    school_response_materials: models.QuerySet["SchoolResponseMaterial"]

    reported_to_school = models.BooleanField(default=False)
    reported_at = PartialDateField(blank=True, default="")

    school_responded_at = PartialDateField(blank=True, default="")  # if known
    school_response = models.TextField(blank=True, default="")

    @property
    def school_responded(self) -> bool:
        return bool(self.school_response)

    def __str__(self) -> str:
        return f"Incident ({self.pk}): {self.occurred_at} {self.school.name} {self.description[:333]}..."


class SupportingMaterial(AttachmentBase):
    """A supporting material for an incident."""

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="supporting_materials"
    )

    class Meta:
        abstract = False


class SchoolResponseMaterial(AttachmentBase):
    """A school response material for an incident."""

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="school_response_materials"
    )

    class Meta:
        abstract = False
