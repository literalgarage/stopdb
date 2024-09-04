from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from .kebab import kebab_to_pascal
from .models import AttachmentBase


def attachment(request: HttpRequest, klass: str, name: str):
    """Serve an attachment by grabbing its binary content from the database."""
    # Convert `klass` from kebab-case to PascalCase.
    model = kebab_to_pascal(klass)

    # Get the attachment model based on `klass`.
    content_type = get_object_or_404(ContentType, app_label="incidents", model=model)
    model_klass = content_type.model_class()
    if model_klass is None:
        raise Http404()

    # Make sure that the model_klass derives from AttachmentBase.
    if not issubclass(model_klass, AttachmentBase):
        raise Http404()

    # Attempt to get the attachment.
    a = get_object_or_404(model_klass, name=name)
    return HttpResponse(a.data, content_type=a.content_type)
