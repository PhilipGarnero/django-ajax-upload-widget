# -*- coding: utf-8 -*-

import os.path
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from itertools import chain
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.core.files import File


class NoDuplicatesFileSystemStorage(FileSystemStorage):
    """Do not save the file if it already exists"""
    def get_available_name(self, name):
        return name

    def _save(self, name, content):
        name = self.get_duplicate_or_new_name(name, content)
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(NoDuplicatesFileSystemStorage, self)._save(name, content)

    def get_duplicate_or_new_name(self, name, content):
        """
        Adds a space and a number to the filename if the filename is taken.
        Increments the number until the new filename is available.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        result_name = name
        i = 0
        # as long as result_name exists increment i and regenerate result_name
        while os.path.exists(self.path(result_name)):
            duplicate = True
            old_content = self.open(result_name)
            content.seek(0)
            while True:
                data_old = old_content.read(File.DEFAULT_CHUNK_SIZE)
                data_new = content.read(File.DEFAULT_CHUNK_SIZE)
                if data_old != data_new:
                    duplicate = False
                    break
                if not data_old or not data_new:
                    break
            if duplicate:
                return result_name
            i += 1
            result_name = os.path.join(dir_name, u"{0} ({1}){2}".format(file_root, i, file_ext))
        return result_name

no_duplicates_protected_media = NoDuplicatesFileSystemStorage(location=settings.PROTECTED_ROOT, 
    base_url=settings.PROTECTED_URL)


no_duplicates_media = NoDuplicatesFileSystemStorage()

def secure_file_delete(sender, instance, **kwargs):
    """Delete a file only if it isn't used by any model"""
    needed_files = []
    for app in settings.INSTALLED_APPS:
        app = os.path.splitext(app)[1][1:] if '.' in app else app
        for model in ContentType.objects.filter(app_label=app):
            mc = model.model_class()
            if mc is None:
                continue

            fields = []
            for field in mc._meta.fields:
                if (field.get_internal_type() == 'FileField' or field.get_internal_type() == 'ImageField'):
                    fields.append(field.name)

            if fields:
                files = list(chain.from_iterable(mc.objects.all().values_list(*fields)))
                needed_files.extend(filter(None, files))

    for storage_field in (x for x in ContentType.objects.get_for_model(instance).model_class()._meta.fields if (hasattr(x, "storage") and isinstance(x.storage, NoDuplicatesFileSystemStorage))):
        if storage_field:
            file = getattr(instance, storage_field.name)
            if file.name not in needed_files:
                file.delete(False)

# You need to place this line under each model using a NoDuplicatesFileSystemStorage 
# post_delete.connect(secure_file_delete, sender=MyModel)
