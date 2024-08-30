from django.contrib import admin
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


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("id", "name")


class ExtraAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value", "has_attachment")
    search_fields = ("id", "name", "value")

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
admin_site.register(Attachment, AttachmentAdmin)
admin_site.register(Extra, ExtraAdmin)
admin_site.register(Link, LinkAdmin)
admin_site.register(SchoolDistrict, SchoolDistrictAdmin)
admin_site.register(School, SchoolAdmin)
admin_site.register(IncidentType, IncidentTypeAdmin)
admin_site.register(SourceType, SourceTypeAdmin)
admin_site.register(Incident, IncidentAdmin)
