from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.is_admin

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow access for admin users or object author
        return request.user.is_authenticated and (
            request.user.is_admin or obj.author == request.user
        )



class IsAdminGetOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == "GET" and request.user.is_authenticated and request.user.is_admin:
            return True

        # Deny access for all other cases
        return False