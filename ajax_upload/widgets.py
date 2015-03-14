import urllib2
import os.path

from django import forms
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from ajax_upload.models import UploadedFile

class AjaxUploadException(Exception):
    pass


class AjaxClearableFileInput(forms.ClearableFileInput):

    class Media:
        js = ("ajax_upload/js/jquery.iframe-transport.js",
              "ajax_upload/js/ajax-upload-widget.js",)
        css = {'all': ('ajax_upload/css/ajax-upload-widget.css',)}

    template_with_clear = ''  # We don't need this
    template_with_initial = '%(input)s'

    def __init__(self, attrs=None, uploader_ops=None, template='ajax_upload_widget.html'):
        super(AjaxClearableFileInput, self).__init__(attrs=attrs)
        self.uploader_ops = uploader_ops or {}
        self.template = template

    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        if value:
            if "/" in value.name:
                filename = u'%s%s' % (UploadedFile._meta.get_field("file").storage.base_url, urllib2.quote(value.name))
            else:
                filename = u'%s%s%s' % (UploadedFile._meta.get_field("file").storage.base_url, UploadedFile._meta.get_field("file").upload_to, urllib2.quote(value.name))
        else:
            filename = ''

        attrs.update({
            'class': attrs.get('class', '') + ' ajax-upload ajax-upload-mark',
            'data-filename': filename,  # This is so the javascript can get the actual value
            'data-required': self.is_required or '',
            'data-upload-url': reverse('ajax-upload')
        })

        return mark_safe(render_to_string(self.template, {
            'input': super(AjaxClearableFileInput, self).render(name, value, attrs),
            'id': self.build_attrs(attrs, type=self.input_type, name=name)['id'],
            'options': self.uploader_ops
        }))

    def value_from_datadict(self, data, files, name):
        # If a file was uploaded or the clear checkbox was checked, use that.
        file = super(AjaxClearableFileInput, self).value_from_datadict(data, files, name)
        if file is not None:  # super class may return a file object, False, or None
            return file  # Default behaviour
        elif name in data:  # This means a file path was specified in the POST field
            file_path = data.get(name)
            if not file_path:
                return False  # False means clear the existing file
            if UploadedFile._meta.get_field("file").upload_to in file_path:
                # Strip and media url to determine the path relative to media url base
                relative_path = file_path[file_path.find(UploadedFile._meta.get_field("file").upload_to):]
                relative_path = urllib2.unquote(relative_path.encode('utf8')).decode('utf8')
                try:
                    uploaded_file = UploadedFile.objects.get(file=relative_path)
                except UploadedFile.DoesNotExist:
                    # Leave the file unchanged (it could be the original file path)
                    return None
                else:
                    file_obj = File(uploaded_file.file)
                    file_obj._size = os.path.getsize(uploaded_file.file.path)
                    file_obj.name = uploaded_file.file.name.split('/')[-1]
                    return file_obj
        return None
