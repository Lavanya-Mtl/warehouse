from django.db import models
from django.conf import settings
from products.models import Product
from boxes.models import Box


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        TO_BE_PACKED = "to_be_packed", "To Be Packed"
        PACKED = "packed", "Packed"
        DISPATCHED = "dispatched", "Dispatched"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        NEEDS_REVIEW = "needs_review", "Needs Manual Review"

    # Valid status transitions
    TRANSITIONS = {
        Status.PENDING: [Status.TO_BE_PACKED, Status.CANCELLED],
        Status.TO_BE_PACKED: [Status.PACKED, Status.CANCELLED],
        Status.PACKED: [Status.DISPATCHED, Status.CANCELLED],
        Status.DISPATCHED: [Status.DELIVERED],
        Status.DELIVERED: [],
        Status.CANCELLED: [],
        Status.NEEDS_REVIEW: [Status.TO_BE_PACKED, Status.CANCELLED],
    }

    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        blank=True,
        default=Status.PENDING,
    )
    recommended_box = models.ForeignKey(
        Box,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    recommendation_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number} — {self.customer_name}"

    def get_allowed_transitions(self):
        return self.TRANSITIONS.get(self.status, [])

    def can_transition_to(self, new_status):
        return new_status in self.get_allowed_transitions()

    @property
    def total_weight_kg(self):
        return sum(
            float(item.product.weight_kg) * item.quantity
            for item in self.items.select_related("product").all()
        )

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def status_badge_class(self):
        mapping = {
            self.Status.PENDING: "bg-yellow-100 text-yellow-800",
            self.Status.TO_BE_PACKED: "bg-blue-100 text-blue-800",
            self.Status.PACKED: "bg-purple-100 text-purple-800",
            self.Status.DISPATCHED: "bg-indigo-100 text-indigo-800",
            self.Status.DELIVERED: "bg-green-100 text-green-800",
            self.Status.CANCELLED: "bg-red-100 text-red-800",
            self.Status.NEEDS_REVIEW: "bg-orange-100 text-orange-800",
        }
        return mapping.get(self.status, "bg-gray-100 text-gray-800")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ["order", "product"]

    def __str__(self):
        return f"{self.quantity}× {self.product.name}"

    @property
    def total_weight_kg(self):
        return float(self.product.weight_kg) * self.quantity