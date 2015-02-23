from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_delete

from ajax_upload.settings import FILE_FIELD_MAX_LENGTH
from .storage import secure_file_delete, no_duplicates_protected_media

class UploadedFile(models.Model):
    creation_date = models.DateTimeField(_('creation date'), auto_now_add=True)
    file = models.FileField(_('file'), max_length=FILE_FIELD_MAX_LENGTH, upload_to='ajax_uploads/', storage=no_duplicates_protected_media)

    class Meta:
        ordering = ('id',)
        verbose_name = _('uploaded file')
        verbose_name_plural = _('uploaded files')

    def __unicode__(self):
        return unicode(self.file)

post_delete.connect(secure_file_delete, sender=UploadedFile)
