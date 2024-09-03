from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from .models import Attachment


def attachment(request: HttpRequest, name: str):
    """Serve an attachment by grabbing its binary content from the database."""
    # NOTE WELL: this is a nice place to start, but we should eventually
    # move attachments to an S3 bucket and use Django Storages to serve them.
    a = get_object_or_404(Attachment, name=name)
    return HttpResponse(a.data, content_type=a.content_type)
