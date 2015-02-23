import json
import urllib2

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler, StopFutureHandlers
from django.conf import settings

from . import settings as upload_settings

from ajax_upload.models import UploadedFile
from ajax_upload.forms import UploadedFileForm


@csrf_exempt
@require_POST
def upload(request):
    url = request.POST.get("url", None)
    if not url:
        form = UploadedFileForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            file_url = uploaded_file.file.url
            try:
                UploadedFile.objects.get(file=uploaded_file.file)
            except UploadedFile.MultipleObjectsReturned:
                uploaded_file.delete()

            data = {
                'path': file_url,
            }
            return HttpResponse(json.dumps(data))
        else:
            return HttpResponseBadRequest(json.dumps({'errors': form.errors}))
    else:
        try:
            # We open the url of the distant file
            distant_file = urllib2.urlopen(url)

            # We check the length of the content (size of the file)
            content_length = int(distant_file.headers.getheader('content-length', settings.FILE_UPLOAD_MAX_MEMORY_SIZE + 1))

            # We get the maximum file upload size
            max_upload_size = getattr(settings, 'AJAX_UPLOAD_MAX_FILESIZE', upload_settings.DEFAULT_MAX_FILESIZE)

            # We check the length of the content
            if 0 < max_upload_size < content_length:
                return HttpResponseBadRequest(json.dumps({'errors': "File too big"}))

            # If it's too big, we store the file on the disk
            if content_length > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
                handler = TemporaryFileUploadHandler()
            # Else, we put it in memory
            else:
                handler = MemoryFileUploadHandler()
                # Attribute activated needed because of the class implementation
                handler.activated = True

            # try/except needed because of the class implementation
            try:
                # Init the file upload handler
                handler.new_file("url", url.split('/')[-1].split('?')[0],
                    distant_file.headers.getheader('content-type'),
                    content_length
                )
            except StopFutureHandlers:
                pass

            def read_in_chunks(file_object, chunk_size=1024):
                """Lazy function to read a file piece by piece."""
                while True:
                    data = file_object.read(chunk_size)
                    if not data:
                        break
                    yield len(data), data

            # We pass all chunks to the file upload handler
            size = 0
            for read, data in read_in_chunks(distant_file, handler.chunk_size):
                handler.receive_data_chunk(data, None)
                size += read

            # We end the handler and save the file to the model
            uploaded_file = UploadedFile()
            uploaded_file.file.save(handler.file_name, handler.file_complete(size))
            uploaded_file.save()
            file_url = uploaded_file.file.url
            try:
                UploadedFile.objects.get(file=uploaded_file.file)
            except UploadedFile.MultipleObjectsReturned:
                uploaded_file.delete()

            data = {
                'path': file_url,
            }
            return HttpResponse(json.dumps(data))
        except Exception:
            return HttpResponseBadRequest(json.dumps({'errors': "An error occured"}))