from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Product
from .forms import ProductForm
from accounts.mixins import ManagerRequiredMixin


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "products/index.html"
    context_object_name = "products"
    paginate_by = 20


class ProductCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"
    success_url = reverse_lazy("product-list")

    def form_valid(self, form):
        messages.success(self.request, "Product created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add Product"
        ctx["action"] = "Create"
        return ctx


class ProductUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"
    success_url = reverse_lazy("product-list")

    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Edit Product"
        ctx["action"] = "Save Changes"
        return ctx


class ProductDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Product
    template_name = "products/confirm_delete.html"
    success_url = reverse_lazy("product-list")

    def form_valid(self, form):
        messages.success(self.request, "Product deleted.")
        return super().form_valid(form)