import uuid

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import UploadedFile
from . import settings as upload_settings


class UploadedFileForm(forms.ModelForm):

    ERRORS = {
        'max_filesize': _('The file is bigger than the maximum size allowed.'),
    }

    class Meta:
        model = UploadedFile
        fields = ('file',)

    def clean_file(self):
        data = self.cleaned_data['file']
        # Change the name of the file to something unguessable
        # Construct the new name as <unique-hex>-<original>.<ext>
        data.name = u'%s-%s' % (uuid.uuid4().hex, data.name)

        max_upload_size = getattr(settings, 'AJAX_UPLOAD_MAX_FILESIZE', upload_settings.DEFAULT_MAX_FILESIZE)
        if 0 < max_upload_size < data.size:
            raise forms.ValidationError(self.ERRORS['max_filesize'])

        return data
