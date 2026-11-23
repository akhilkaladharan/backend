from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


class SimpleCorsMiddleware:
    """Minimal CORS support so the React app can call the API from another origin.

    Only origins listed in settings.CORS_ALLOWED_ORIGINS are allowed. Because
    authentication uses an Authorization header (not cookies), credentials are
    never shared across origins.
    """

    ALLOW_HEADERS = "Authorization, Content-Type"
    ALLOW_METHODS = "GET, POST, PATCH, DELETE, OPTIONS"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        allowed = bool(origin) and origin in settings.CORS_ALLOWED_ORIGINS

        is_preflight = (
            request.method == "OPTIONS"
            and "Access-Control-Request-Method" in request.headers
        )
        if is_preflight and allowed:
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        patch_vary_headers(response, ["Origin"])
        if allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Headers"] = self.ALLOW_HEADERS
            response["Access-Control-Allow-Methods"] = self.ALLOW_METHODS
            response["Access-Control-Max-Age"] = "86400"
        return response
