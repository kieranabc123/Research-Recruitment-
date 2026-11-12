# Role check for views, for example @role_required("researcher", approved=True)
# Logged out people go to the login page and the wrong role gets the 403 page.
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles, approved=False):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            if approved and not request.user.approved:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
