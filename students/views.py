import json
import re

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth import is_teacher, make_token, student_required, teacher_required, token_required
from .forms import ApplicationForm
from .models import COURSES, Application, Message

User = get_user_model()

MESSAGE_MAX_LENGTH = 1000
REMARKS_MAX_LENGTH = 1000


# --- helpers ---------------------------------------------------------------
def _json_body(request):
    """Parse a JSON request body. Returns a dict, or None if it is invalid."""
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _bad_request(detail="Invalid request."):
    return JsonResponse({"detail": detail}, status=400)


def _form_errors(form):
    return {field: [str(e) for e in errs] for field, errs in form.errors.items()}


def serialize_user(user):
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "role": "teacher" if is_teacher(user) else "student",
    }


def serialize_application(app):
    return {
        "id": app.pk,
        "username": app.user.username,
        "full_name": app.full_name,
        "email": app.email,
        "phone": app.phone,
        "date_of_birth": app.date_of_birth.isoformat(),
        "address": app.address,
        "guardian_name": app.guardian_name,
        "course": app.course,
        # Relative URL (e.g. /media/photos/abc.jpg); the frontend adds the host.
        "photo_url": app.photo.url if app.photo else None,
        "status": app.status,
        "teacher_remarks": app.teacher_remarks,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
    }


def serialize_message(msg):
    return {
        "id": msg.pk,
        "sender": msg.sender.username,
        "sender_role": "teacher" if is_teacher(msg.sender) else "student",
        "body": msg.body,
        "created_at": msg.created_at.isoformat(),
    }


# --- auth ------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Students create their own account. Teacher accounts are made by an admin."""
    data = _json_body(request)
    if data is None:
        return _bad_request("Invalid JSON.")

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))
    errors = {}

    if not re.fullmatch(r"[\w.+-]{3,30}", username):
        errors["username"] = [
            "Use 3-30 letters, numbers or . _ + - (no spaces)."
        ]
    elif User.objects.filter(username__iexact=username).exists():
        errors["username"] = ["This username is already taken."]

    try:
        validate_email(email)
    except ValidationError:
        errors["email"] = ["Enter a valid email address."]

    try:
        validate_password(password, user=User(username=username, email=email))
    except ValidationError as exc:
        errors["password"] = list(exc.messages)

    if errors:
        return JsonResponse({"detail": "Please fix the errors below.", "errors": errors}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    return JsonResponse(
        {"token": make_token(user), "user": serialize_user(user)}, status=201
    )


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    data = _json_body(request)
    if data is None:
        return _bad_request("Invalid JSON.")
    user = authenticate(
        username=str(data.get("username", "")).strip(),
        password=str(data.get("password", "")),
    )
    if user is None:
        return _bad_request("Invalid username or password.")
    return JsonResponse({"token": make_token(user), "user": serialize_user(user)})


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def me(request):
    return JsonResponse(serialize_user(request.user))


@require_http_methods(["GET"])
def courses(request):
    return JsonResponse({"courses": COURSES})


# --- student ---------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET", "POST"])
@student_required
def my_application(request):
    """GET: the logged-in student's application (or null).
    POST (multipart/form-data): create it, or update it while still pending."""
    app = Application.objects.select_related("user").filter(user=request.user).first()

    if request.method == "GET":
        return JsonResponse(
            {"application": serialize_application(app) if app else None}
        )

    if app and app.status != Application.Status.PENDING:
        return JsonResponse(
            {"detail": "Your application has already been reviewed and can't be edited."},
            status=403,
        )

    created = app is None
    old_photo = app.photo.name if app and app.photo else None

    form = ApplicationForm(request.POST, request.FILES, instance=app)
    if not form.is_valid():
        return JsonResponse(
            {"detail": "Please fix the errors below.", "errors": _form_errors(form)},
            status=400,
        )

    saved = form.save(commit=False)
    saved.user = request.user
    saved.save()

    # Remove the replaced photo from disk.
    if old_photo and old_photo != saved.photo.name:
        saved.photo.storage.delete(old_photo)

    return JsonResponse(
        {"application": serialize_application(saved)}, status=201 if created else 200
    )


# --- messages (student <-> teacher) ---------------------------------------
def _application_for_user(request, pk):
    """Teachers can open any application; students only their own."""
    qs = Application.objects.select_related("user")
    if not is_teacher(request.user):
        qs = qs.filter(user=request.user)
    return qs.filter(pk=pk).first()


@csrf_exempt
@require_http_methods(["GET", "POST"])
@token_required
def messages_view(request, pk):
    app = _application_for_user(request, pk)
    if app is None:
        return JsonResponse({"detail": "Application not found."}, status=404)

    if request.method == "GET":
        msgs = app.messages.select_related("sender")
        return JsonResponse({"messages": [serialize_message(m) for m in msgs]})

    data = _json_body(request)
    if data is None:
        return _bad_request("Invalid JSON.")
    body = str(data.get("body", "")).strip()
    if not body:
        return _bad_request("Write a message first.")
    if len(body) > MESSAGE_MAX_LENGTH:
        return _bad_request(f"Messages can be at most {MESSAGE_MAX_LENGTH} characters.")

    msg = Message.objects.create(application=app, sender=request.user, body=body)
    return JsonResponse({"message": serialize_message(msg)}, status=201)


# --- teacher ---------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
@teacher_required
def teacher_list(request):
    base = Application.objects.select_related("user")
    counts = {
        "all": base.count(),
        **{value: base.filter(status=value).count() for value, _ in Application.Status.choices},
    }

    qs = base
    status = request.GET.get("status", "").strip()
    if status in Application.Status.values:
        qs = qs.filter(status=status)

    search = request.GET.get("q", "").strip()
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search)
            | Q(email__icontains=search)
            | Q(course__icontains=search)
            | Q(user__username__icontains=search)
        )

    return JsonResponse(
        {"counts": counts, "applications": [serialize_application(a) for a in qs]}
    )


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
@teacher_required
def teacher_detail(request, pk):
    app = Application.objects.select_related("user").filter(pk=pk).first()
    if app is None:
        return JsonResponse({"detail": "Application not found."}, status=404)

    if request.method == "GET":
        return JsonResponse({"application": serialize_application(app)})

    if request.method == "DELETE":
        app.photo.delete(save=False)
        app.delete()
        return HttpResponse(status=204)

    # PATCH: update status and/or remarks
    data = _json_body(request)
    if data is None:
        return _bad_request("Invalid JSON.")

    update_fields = []
    if "status" in data:
        if data["status"] not in Application.Status.values:
            return _bad_request("Status must be pending, approved or rejected.")
        app.status = data["status"]
        update_fields.append("status")
    if "teacher_remarks" in data:
        remarks = str(data["teacher_remarks"]).strip()
        if len(remarks) > REMARKS_MAX_LENGTH:
            return _bad_request(f"Remarks can be at most {REMARKS_MAX_LENGTH} characters.")
        app.teacher_remarks = remarks
        update_fields.append("teacher_remarks")

    if update_fields:
        app.save(update_fields=update_fields + ["updated_at"])
    return JsonResponse({"application": serialize_application(app)})
