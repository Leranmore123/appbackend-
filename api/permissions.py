from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access to users with role in ('admin', 'trainer', 'faculty') or is_staff."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'role', '') in ('admin', 'trainer', 'faculty')
                or getattr(request.user, 'is_staff', False)
                or getattr(request.user, 'is_superuser', False)
            )
        )
