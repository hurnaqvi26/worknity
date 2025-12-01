from django.core.exceptions import PermissionDenied
from accounts.models import EmployeeProfile


def user_role(user):
    """Return the role of the logged-in user."""
    try:
        return EmployeeProfile.objects.get(user=user).role
    except EmployeeProfile.DoesNotExist:
        return None


def role_required(allowed_roles):
    """
    Decorator to protect views based on user roles.
    Example: @role_required(["ADMIN"])
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = user_role(request.user)
            if role not in allowed_roles:
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
