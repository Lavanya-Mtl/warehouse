from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.shortcuts import redirect


class ManagerRequiredMixin(AccessMixin):
    """Restrict view to users with Manager role."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_manager() and not request.user.is_superuser:
            messages.error(request, "You need manager permissions to do that.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)