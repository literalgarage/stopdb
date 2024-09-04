from django.urls import path

from .views import attachment

app_name = "incidents"
urlpatterns = [
    path("a/<str:klass>/<str:name>", attachment, name="attachment"),
]
