"""Token authentication using Django's signed values (no extra packages)."""
from functools import wraps

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.http import JsonResponse

TOKEN_SALT = "students.auth.token"


def make_token(user):
    return signing.dumps({"uid": user.pk}, salt=TOKEN_SALT)


def user_from_request(request):
    """Return the user for the `Authorization: Bearer <token>` header, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[len("Bearer "):].strip()
    try:
        data = signing.loads(
            token, salt=TOKEN_SALT, max_age=settings.AUTH_TOKEN_MAX_AGE
        )
    except signing.BadSignature:  # also covers expired tokens
        return None
    User = get_user_model()
    try:
        return User.objects.get(pk=data.get("uid"), is_active=True)
    except User.DoesNotExist:
        return None


def is_teacher(user):
    return user.is_staff


def _deny(detail, status):
    return JsonResponse({"detail": detail}, status=status)


def token_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = user_from_request(request)
        if user is None:
            return _deny("Authentication required.", 401)
        request.user = user
        return view(request, *args, **kwargs)

    return wrapper


def teacher_required(view):
    @wraps(view)
    @token_required
    def wrapper(request, *args, **kwargs):
        if not is_teacher(request.user):
            return _deny("Teacher access only.", 403)
        return view(request, *args, **kwargs)

    return wrapper


def student_required(view):
    @wraps(view)
    @token_required
    def wrapper(request, *args, **kwargs):
        if is_teacher(request.user):
            return _deny("This page is for students.", 403)
        return view(request, *args, **kwargs)

    return wrapper
