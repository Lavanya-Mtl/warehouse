"""
Integration tests for key views.
"""
import pytest
from django.urls import reverse
from tests.factories import (
    UserFactory, ManagerFactory, ProductFactory,
    BoxFactory, OrderFactory, OrderItemFactory,
)
from orders.models import Order


pytestmark = pytest.mark.django_db


class TestAuthRequirement:
    """All views should redirect unauthenticated users to login."""

    def test_dashboard_requires_login(self, client):
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_order_list_requires_login(self, client):
        response = client.get(reverse("order-list"))
        assert response.status_code == 302

    def test_product_list_requires_login(self, client):
        response = client.get(reverse("product-list"))
        assert response.status_code == 302

    def test_box_list_requires_login(self, client):
        response = client.get(reverse("box-list"))
        assert response.status_code == 302


class TestDashboard:
    def test_staff_can_view_dashboard(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_dashboard_shows_order_columns(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("dashboard"))
        assert b"To Be Packed" in response.content or b"Pending" in response.content


class TestOrderViews:
    def test_order_list_accessible_to_staff(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("order-list"))
        assert response.status_code == 200

    def test_order_list_shows_orders(self, client):
        user = UserFactory()
        order = OrderFactory(customer_name="Alice Smith")
        client.force_login(user)
        response = client.get(reverse("order-list"))
        assert b"Alice Smith" in response.content

    def test_order_detail_accessible(self, client):
        user = UserFactory()
        order = OrderFactory()
        client.force_login(user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert response.status_code == 200

    def test_order_detail_shows_order_number(self, client):
        user = UserFactory()
        order = OrderFactory(order_number="ORD-99999")
        client.force_login(user)
        response = client.get(reverse("order-detail", kwargs={"pk": order.pk}))
        assert b"ORD-99999" in response.content

    def test_order_status_filter(self, client):
        user = UserFactory()
        OrderFactory(status=Order.Status.PENDING)
        OrderFactory(status=Order.Status.PACKED)
        client.force_login(user)
        response = client.get(reverse("order-list") + "?status=packed")
        assert response.status_code == 200

    def test_valid_status_transition(self, client):
        user = UserFactory()
        order = OrderFactory(status=Order.Status.PENDING)
        client.force_login(user)
        response = client.post(
            reverse("order-transition", kwargs={"pk": order.pk, "new_status": "to_be_packed"})
        )
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.status == Order.Status.TO_BE_PACKED

    def test_invalid_status_transition_rejected(self, client):
        user = UserFactory()
        order = OrderFactory(status=Order.Status.PENDING)
        client.force_login(user)
        client.post(
            reverse("order-transition", kwargs={"pk": order.pk, "new_status": "delivered"})
        )
        order.refresh_from_db()
        # Should NOT have changed
        assert order.status == Order.Status.PENDING

    def test_re_recommend_updates_box(self, client):
        user = UserFactory()
        product = ProductFactory(
            length_cm=10, width_cm=8, height_cm=5, weight_kg=0.5
        )
        box = BoxFactory(
            internal_length_cm=50, internal_width_cm=40,
            internal_height_cm=30, max_weight_kg=10, is_active=True
        )
        order = OrderFactory(status=Order.Status.PENDING)
        OrderItemFactory(order=order, product=product, quantity=1)
        client.force_login(user)
        response = client.get(reverse("order-re-recommend", kwargs={"pk": order.pk}))
        assert response.status_code == 302
        order.refresh_from_db()
        assert order.recommended_box is not None


class TestProductViews:
    def test_product_list_accessible_to_staff(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("product-list"))
        assert response.status_code == 200

    def test_staff_cannot_create_product(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("product-create"))
        assert response.status_code == 302  # redirected away

    def test_manager_can_create_product(self, client):
        manager = ManagerFactory()
        client.force_login(manager)
        response = client.get(reverse("product-create"))
        assert response.status_code == 200

    def test_manager_can_post_new_product(self, client):
        manager = ManagerFactory()
        client.force_login(manager)
        response = client.post(reverse("product-create"), {
            "name": "New Widget",
            "sku": "NW-001",
            "length_cm": "10.00",
            "width_cm": "8.00",
            "height_cm": "5.00",
            "weight_kg": "0.300",
            "description": "",
        })
        assert response.status_code == 302
        from products.models import Product
        assert Product.objects.filter(sku="NW-001").exists()


class TestBoxViews:
    def test_box_list_accessible_to_staff(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("box-list"))
        assert response.status_code == 200

    def test_staff_cannot_create_box(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("box-create"))
        assert response.status_code == 302

    def test_manager_can_create_box(self, client):
        manager = ManagerFactory()
        client.force_login(manager)
        response = client.get(reverse("box-create"))
        assert response.status_code == 200

    def test_box_list_shows_boxes(self, client):
        user = UserFactory()
        BoxFactory(name="My Test Box")
        client.force_login(user)
        response = client.get(reverse("box-list"))
        assert b"My Test Box" in response.content