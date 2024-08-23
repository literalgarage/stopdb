from mimetypes import guess_type

from django.core.exceptions import ValidationError
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Attachment(models.Model):
    name = models.CharField(max_length=100, help_text="Includes file extension")
    data = models.BinaryField()

    @property
    def content_type(self) -> str | None:
        return guess_type(self.name)[0]


class Extra(models.Model):
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


class Link(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")
    url = models.URLField()


class SchoolDistrict(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ForeignKey(
        Attachment,
        default=None,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logos_of_districts",
    )
    url = models.URLField()
    twitter = models.URLField(blank=True, default="")
    facebook = models.URLField(blank=True, default="")
    phone = PhoneNumberField(blank=True, default="")

    superintendent_name = models.CharField(max_length=100)
    superintendent_email = models.EmailField()

    civil_rights_url = models.URLField(blank=True)
    civil_rights_contact_name = models.CharField(max_length=100, blank=True)
    civil_rights_contact_email = models.EmailField(blank=True)

    hib_url = models.URLField(blank=True)
    hib_form_url = models.URLField(blank=True)
    hib_contact_name = models.CharField(max_length=100, blank=True)
    hib_contact_email = models.EmailField(blank=True)

    board_url = models.URLField(blank=True)

    extras = models.ManyToManyField(Extra, blank=True, related_name="district_extras")


class School(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    district = models.ForeignKey(
        SchoolDistrict,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="schools",
    )
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=5)
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


class IncidentType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")


class SourceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")


class Incident(models.Model):
    description = models.TextField()

    submitted_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(null=True, blank=True, default=None)

    @property
    def is_published(self) -> bool:
        return self.published_at is not None

    # TODO: future migration

    # published_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="publisher",
    # )

    # group = models.ForeignKey(
    #     Group,
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="incidents",
    # )

    # Potentially partial date when the incident occurred
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="incidents"
    )
    incident_types = models.ManyToManyField(IncidentType)
    source_types = models.ManyToManyField(SourceType)

    related_links = models.ManyToManyField(Link, blank=True, related_name="incidents")
    supporting_materials = models.ManyToManyField(
        Attachment, blank=True, related_name="supporting_materials"
    )

    reported_to_school = models.BooleanField()
    reported_year = models.IntegerField(null=True, blank=True, default=None)
    reported_month = models.IntegerField(null=True, blank=True, default=None)
    reported_day = models.IntegerField(null=True, blank=True, default=None)

    school_responded = models.BooleanField()
    school_response_year = models.IntegerField(null=True, blank=True, default=None)
    school_response_month = models.IntegerField(null=True, blank=True, default=None)
    school_response_day = models.IntegerField(null=True, blank=True, default=None)
    school_response = models.TextField(blank=True, default="")
    school_response_materials = models.ManyToManyField(
        Attachment, blank=True, related_name="school_response_materials"
    )

    extras = models.ManyToManyField(Extra)
