from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction

from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet
from boxes.models import Box
from recommender.service import recommend_box, items_from_order


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        qs = Order.objects.select_related("recommended_box", "created_by")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Order.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related(
            "recommended_box", "created_by"
        ).prefetch_related("items__product")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["allowed_transitions"] = self.object.get_allowed_transitions()
        ctx["status_labels"] = dict(Order.Status.choices)
        return ctx


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["item_formset"] = OrderItemFormSet(self.request.POST)
        else:
            ctx["item_formset"] = OrderItemFormSet()
        ctx["title"] = "New Order"
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        
        ctx = self.get_context_data()
        item_formset = ctx["item_formset"]
        print(self.request.POST)
        print(item_formset.errors)
        if not item_formset.is_valid():
            return self.form_invalid(form)

        order = form.save(commit=False)
        order.created_by = self.request.user
        order.save()

        item_formset.instance = order
        item_formset.save()

        # Run box recommendation
        _run_recommendation(order)
        order.save()

        messages.success(
            self.request,
            f"Order #{order.order_number} created. "
            + (
                f"Recommended box: {order.recommended_box.name}"
                if order.recommended_box
                else "⚠ No suitable box found — manual review needed."
            ),
        )
        return redirect(reverse("order-detail", kwargs={"pk": order.pk}))


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["item_formset"] = OrderItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            ctx["item_formset"] = OrderItemFormSet(instance=self.object)
        ctx["title"] = "Edit Order"
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        ctx = self.get_context_data()
        item_formset = ctx["item_formset"]

        if not item_formset.is_valid():
            return self.form_invalid(form)

        order = form.save()
        item_formset.instance = order
        item_formset.save()

        # Re-run recommendation after edits
        _run_recommendation(order)
        order.save()

        messages.success(self.request, "Order updated and recommendation refreshed.")
        return redirect(reverse("order-detail", kwargs={"pk": order.pk}))

    def get_success_url(self):
        return reverse("order-detail", kwargs={"pk": self.object.pk})


@login_required
def order_transition(request, pk, new_status):
    """Handle order status transitions."""
    order = get_object_or_404(Order, pk=pk)

    if request.method != "POST":
        return redirect("order-detail", pk=pk)

    if not order.can_transition_to(new_status):
        messages.error(
            request,
            f"Cannot move order to '{new_status}' from '{order.status}'.",
        )
        return redirect("order-detail", pk=pk)

    order.status = new_status
    order.save()
    status_label = dict(Order.Status.choices).get(new_status, new_status)
    messages.success(request, f"Order status updated to: {status_label}")
    return redirect("order-detail", pk=pk)


@login_required
def order_re_recommend(request, pk):
    """Re-run the box recommendation for an order."""
    order = get_object_or_404(Order, pk=pk)
    _run_recommendation(order)
    order.save()
    if order.recommended_box:
        messages.success(
            request, f"Recommendation updated: {order.recommended_box.name}"
        )
    else:
        messages.warning(request, f"No suitable box found. {order.recommendation_reason}")
    return redirect("order-detail", pk=pk)


def _run_recommendation(order):
    """Internal helper: run recommender and update order fields."""
    items = items_from_order(order)
    boxes = Box.objects.filter(is_active=True).order_by("cost_rupees")
    result = recommend_box(items, boxes)

    order.recommended_box = result.recommended_box
    order.recommendation_reason = result.reason
    if not result.success:
        order.status = Order.Status.NEEDS_REVIEW


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "orders/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Orders grouped by status for the dashboard columns
        active_statuses = [
            Order.Status.NEEDS_REVIEW,
            Order.Status.PENDING,
            Order.Status.TO_BE_PACKED,
            Order.Status.PACKED,
            Order.Status.DISPATCHED,
        ]

        columns = []
        for status in active_statuses:
            orders = Order.objects.filter(status=status).select_related(
                "recommended_box"
            ).prefetch_related("items")[:10]
            columns.append({
                "status": status,
                "label": dict(Order.Status.choices)[status],
                "orders": list(orders),
                "count": Order.objects.filter(status=status).count(),
            })

        ctx["columns"] = columns
        ctx["total_orders"] = Order.objects.count()
        ctx["delivered_today"] = Order.objects.filter(
            status=Order.Status.DELIVERED
        ).count()
        ctx["needs_review"] = Order.objects.filter(
            status=Order.Status.NEEDS_REVIEW
        ).count()
        return ctx