import os
import uuid

from django.conf import settings
from django.db import models

# Courses a student can apply for. Edit this list to match your institution.
COURSES = [
    "Cloud Computing",
    "Web Development",
    "Data Science",
    "Cyber Security",
    "Networking",
    "Other",
]
COURSE_CHOICES = [(c, c) for c in COURSES]


def photo_upload_path(instance, filename):
    """Store photos under a random name so file names can't clash or leak."""
    ext = os.path.splitext(filename)[1].lower()
    return f"photos/{uuid.uuid4().hex}{ext}"


class Application(models.Model):
    """A student's application. Each student has exactly one."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    address = models.TextField()
    guardian_name = models.CharField(max_length=120, blank=True)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    photo = models.ImageField(upload_to=photo_upload_path)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    teacher_remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"


class Message(models.Model):
    """A message in the conversation between a student and the teachers."""

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.sender} on application {self.application_id}"
