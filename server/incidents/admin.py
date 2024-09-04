import typing as t

from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.files import File
from django.utils.safestring import mark_safe

from server.admin import admin_site

from .models import (
    AttachmentBase,
    DistrictLogo,
    Incident,
    IncidentExtra,
    IncidentType,
    Region,
    RelatedLink,
    School,
    SchoolDistrict,
    SchoolResponseMaterial,
    SourceType,
    SupportingMaterial,
)

# -----------------------------------------------------------------------------
# Abstract base admin classes
# -----------------------------------------------------------------------------


class AttachmentFormBase(forms.ModelForm):
    """Arbitrary attachment form."""

    class Meta:
        """Meta class."""

        # derived classes: add a model =
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


class AttachmentAdminBase(admin.TabularInline):
    # derived classes: Add a model = and a form =
    fields = ("name", "attachment_display", "choose_file")
    readonly_fields = ("attachment_display",)
    extra = 0

    @admin.display(description="Image or download link")
    def attachment_display(self, obj: AttachmentBase):
        if obj.url is None:
            return ""
        if obj.is_image:
            return mark_safe(f'<img src="{obj.url}" style="max-width: 72px;">')
        return mark_safe(f'<a href="{obj.url}">{obj.name}</a>')


class ExtraAdminBase(admin.TabularInline):
    list_display = ("name", "value")
    search_fields = ("name", "value")
    extra = 0


# -----------------------------------------------------------------------------
# Concrete admin classes: Region
# -----------------------------------------------------------------------------


class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("id", "name")
    readonly_fields = ("group",)

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


# -----------------------------------------------------------------------------
# Concrete admin classes: School District & School
# -----------------------------------------------------------------------------


class DistrictLogoAdminForm(AttachmentFormBase):
    class Meta(AttachmentFormBase.Meta):
        model = DistrictLogo


class DistrictLogoAdmin(AttachmentAdminBase):
    model = DistrictLogo
    form = DistrictLogoAdminForm
    extra = 0


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
    inlines = [DistrictLogoAdmin]


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


# -----------------------------------------------------------------------------
# Concrete admin classes: Incident & related models
# -----------------------------------------------------------------------------


class RelatedLinkAdmin(admin.TabularInline):
    model = RelatedLink
    list_display = ("name", "url")
    search_fields = ("name", "url")
    extra = 0


class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


class SourceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


class SupportingMaterialForm(AttachmentFormBase):
    class Meta(AttachmentFormBase.Meta):
        model = SupportingMaterial


class SupportingMaterialAdmin(AttachmentAdminBase):
    model = SupportingMaterial
    form = SupportingMaterialForm


class SchoolResponseMaterialForm(AttachmentFormBase):
    class Meta(AttachmentFormBase.Meta):
        model = SchoolResponseMaterial


class SchoolResponseMaterialAdmin(AttachmentAdminBase):
    model = SchoolResponseMaterial
    form = SchoolResponseMaterialForm


class IncidentExtraAdmin(ExtraAdminBase):
    model = IncidentExtra


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
    inlines = [
        SupportingMaterialAdmin,
        SchoolResponseMaterialAdmin,
        RelatedLinkAdmin,
        IncidentExtraAdmin,
    ]

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
admin_site.register(SchoolDistrict, SchoolDistrictAdmin)
admin_site.register(School, SchoolAdmin)
admin_site.register(IncidentType, IncidentTypeAdmin)
admin_site.register(SourceType, SourceTypeAdmin)
admin_site.register(Incident, IncidentAdmin)
