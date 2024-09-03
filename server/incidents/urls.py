from django.urls import path

from .views import attachment

app_name = "incidents"
urlpatterns = [
    path("attachment/<str:name>", attachment, name="attachment"),
]
