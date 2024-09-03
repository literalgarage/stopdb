import typing as t

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.files import File
from django.urls import reverse
from django.utils.safestring import mark_safe

from server.admin import admin_site

from .models import (
    Attachment,
    Extra,
    Incident,
    IncidentType,
    Link,
    Region,
    School,
    SchoolDistrict,
    SourceType,
)


class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("id", "name")

    def save_model(self, request, obj: Region, form, change):
        # If we're creating a new region, we'll need to create a group
        if not change:
            name = obj.name
            group, _ = Group.objects.get_or_create(name=Region.default_group_name(name))
            obj.group = group

        # Save the region
        super().save_model(request, obj, form, change)

        # If we're changing the region, we need to make sure the group name is in sync
        if change:
            group = obj.group
            group.name = Region.default_group_name(obj.name)
            group.save()


class AttachmentForm(forms.ModelForm):
    """Arbitrary attachment form."""

    class Meta:
        """Meta class."""

        model = Attachment
        fields = ("choose_file", "name")
        readonly_fields = ("name",)

    choose_file = forms.FileField(required=False)

    def save(self, *args: t.Any, **kwargs: t.Any):
        """Save the form."""
        choose_file = self.cleaned_data.pop("choose_file", None)
        if choose_file is not None:
            assert isinstance(choose_file, File)
            self.instance.name = choose_file.name
            self.instance.data = choose_file.read()
        return super().save(*args, **kwargs)


class AttachmentAdmin(admin.TabularInline):
    model = Attachment
    form = AttachmentForm
    fields = ("name", "attachment_display", "choose_file")
    readonly_fields = ("attachment_display",)

    @admin.display(description="Attachment")
    def attachment_display(self, obj: Attachment):
        attachment_url = reverse("incidents:attachment", args=[obj.name])
        if obj.is_image:
            return mark_safe(f'<img src="{attachment_url}" style="max-width: 72px;">')
        return mark_safe(f'<a href="{attachment_url}">{obj.name}</a>')


class ZeroOrOneAttachmentAdmin(AttachmentAdmin):
    extra = 0


class ExtraAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value", "has_attachment")
    search_fields = ("id", "name", "value")
    inlines = [ZeroOrOneAttachmentAdmin]

    def has_attachment(self, obj):
        return obj.attachment is not None


class LinkAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url")
    search_fields = ("id", "name", "url")


class SchoolDistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    search_fields = (
        "id",
        "name",
        "phone",
        "superintendent_name",
        "superintendent_email",
        "civil_rights_contact_name",
        "civil_rights_contact_email",
        "hib_contact_name",
        "hib_contact_email",
    )


class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "state",
        "is_public",
        "is_elementary",
        "is_middle",
        "is_high",
        "district_link",
    )
    search_fields = ("id", "name", "url", "district__name", "city", "state")

    def district_link(self, obj):
        if not obj.district:
            return ""
        return mark_safe(
            f'<a href="/admin/incidents/schooldistrict/{obj.district.id}/change/">{obj.district.name}</a>'
        )

    district_link.allow_tags = True


class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


class SourceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "occurred_at",
        "published_at",
        "incident_types_list",
        "source_types_list",
        "description_short",
        "school_link",
    )
    search_fields = (
        "id",
        "description",
        "school__name",
        "school__city",
        "school__state",
    )

    def incident_types_list(self, obj):
        return ", ".join(
            [incident_type.name for incident_type in obj.incident_types.all()]
        )

    def source_types_list(self, obj):
        return ", ".join([source_type.name for source_type in obj.source_types.all()])

    def description_short(self, obj):
        return (
            obj.description[:50] + "..."
            if len(obj.description) > 50
            else obj.description
        )

    def school_link(self, obj):
        return mark_safe(
            f'<a href="/admin/incidents/school/{obj.school.id}/change/">{obj.school.name}</a>'
        )

    school_link.allow_tags = True


admin_site.register(Region, RegionAdmin)
# admin_site.register(Attachment, AttachmentAdmin)
admin_site.register(Extra, ExtraAdmin)
admin_site.register(Link, LinkAdmin)
admin_site.register(SchoolDistrict, SchoolDistrictAdmin)
admin_site.register(School, SchoolAdmin)
admin_site.register(IncidentType, IncidentTypeAdmin)
admin_site.register(SourceType, SourceTypeAdmin)
admin_site.register(Incident, IncidentAdmin)
