import re

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from .models import Application


class ApplicationForm(forms.ModelForm):
    """Validates the multipart form a student submits (including the photo)."""

    class Meta:
        model = Application
        fields = [
            "full_name",
            "email",
            "phone",
            "date_of_birth",
            "address",
            "guardian_name",
            "course",
            "photo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing, the student may keep their existing photo.
        if self.instance and self.instance.pk:
            self.fields["photo"].required = False

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not re.fullmatch(r"[0-9+\-\s]{7,20}", phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        if dob >= timezone.localdate():
            raise forms.ValidationError("Date of birth must be in the past.")
        return dob

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        # Only a freshly uploaded file needs the size check; when no new file
        # is sent, Django hands back the stored one.
        if isinstance(photo, UploadedFile) and photo.size > settings.PHOTO_MAX_BYTES:
            limit_mb = settings.PHOTO_MAX_BYTES // (1024 * 1024)
            raise forms.ValidationError(f"Photo must be {limit_mb} MB or smaller.")
        return photo
