from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a demo teacher and a demo student (for development only)."

    def add_arguments(self, parser):
        parser.add_argument("--teacher-password", default="teacher123")
        parser.add_argument("--student-password", default="student123")

    def handle(self, *args, **options):
        User = get_user_model()

        teacher, created = User.objects.get_or_create(
            username="teacher",
            defaults={"email": "teacher@example.com", "is_staff": True},
        )
        if created:
            teacher.set_password(options["teacher_password"])
            teacher.save()
        self._report("teacher", options["teacher_password"], created)

        student, created = User.objects.get_or_create(
            username="student", defaults={"email": "student@example.com"}
        )
        if created:
            student.set_password(options["student_password"])
            student.save()
        self._report("student", options["student_password"], created)

        self.stdout.write(
            self.style.WARNING("Demo accounts are for development. Don't use them in production.")
        )

    def _report(self, username, password, created):
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {username} / {password}"))
        else:
            self.stdout.write(f"{username} already exists - left unchanged")
