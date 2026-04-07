from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Only admin users can access this endpoint.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


class IsUser(permissions.BasePermission):
    """
    Only authenticated users (admin or regular user) can access.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - Admin users can create, update, delete
    - All authenticated users can read
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )
