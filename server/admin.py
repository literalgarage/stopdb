from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext_lazy as _


class AdminSite(admin.AdminSite):
    site_title = _("Stop Hate In Schools -- Administration")
    site_header = _("Stop Hate In Schools -- Administration")
    index_title = _("Stop Hate In Schools -- Administration")


admin_site = AdminSite()
admin_site.enable_nav_sidebar = False
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
