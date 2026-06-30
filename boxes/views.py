from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Box
from .forms import BoxForm
from accounts.mixins import ManagerRequiredMixin


class BoxListView(LoginRequiredMixin, ListView):
    model = Box
    template_name = "boxes/list.html"
    context_object_name = "boxes"

    def get_queryset(self):
        return Box.objects.all().order_by("cost_rupees")


class BoxCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Box
    form_class = BoxForm
    template_name = "boxes/form.html"
    success_url = reverse_lazy("box-list")

    def form_valid(self, form):
        messages.success(self.request, "Box created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add Box"
        ctx["action"] = "Create"
        return ctx


class BoxUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Box
    form_class = BoxForm
    template_name = "boxes/form.html"
    success_url = reverse_lazy("box-list")

    def form_valid(self, form):
        messages.success(self.request, "Box updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Edit Box"
        ctx["action"] = "Save Changes"
        return ctx


class BoxDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Box
    template_name = "boxes/confirm_delete.html"
    success_url = reverse_lazy("box-list")

    def form_valid(self, form):
        messages.success(self.request, "Box deleted.")
        return super().form_valid(form)