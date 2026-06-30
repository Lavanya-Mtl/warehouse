"""
Tests for Order, Product, and Box models.
"""
import pytest
from decimal import Decimal
from tests.factories import (
    UserFactory, ManagerFactory, ProductFactory,
    BoxFactory, OrderFactory, OrderItemFactory,
)
from orders.models import Order
from accounts.models import User


pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_staff_user_is_not_manager(self):
        user = UserFactory(role=User.Role.WAREHOUSE_STAFF)
        assert user.is_manager() is False

    def test_manager_user_is_manager(self):
        user = ManagerFactory()
        assert user.is_manager() is True

    def test_str_representation(self):
        user = UserFactory(username="jdoe", first_name="Jane", last_name="Doe")
        assert "Jane Doe" in str(user)


class TestProductModel:
    def test_volume_calculated_correctly(self):
        product = ProductFactory(length_cm=10, width_cm=5, height_cm=4)
        assert product.volume_cm3 == pytest.approx(200.0)

    def test_str_includes_sku(self):
        product = ProductFactory(name="Test Widget", sku="PRD-001")
        assert "Test Widget" in str(product)
        assert "PRD-001" in str(product)


class TestBoxModel:
    def test_volume_calculated_correctly(self):
        box = BoxFactory(
            internal_length_cm=50,
            internal_width_cm=40,
            internal_height_cm=30,
        )
        assert box.volume_cm3 == pytest.approx(60000.0)

    def test_cost_display_format(self):
        box = BoxFactory(cost_rupees=150)
        assert box.cost_display == "INR 150.00"

    def test_cost_display_zero_rupees(self):
        box = BoxFactory(cost_rupees=200)
        assert box.cost_display == "INR 200.00"


class TestOrderModel:
    def test_order_transitions_from_pending(self):
        order = OrderFactory(status=Order.Status.PENDING)
        assert order.can_transition_to(Order.Status.TO_BE_PACKED) is True
        assert order.can_transition_to(Order.Status.CANCELLED) is True
        assert order.can_transition_to(Order.Status.PACKED) is False
        assert order.can_transition_to(Order.Status.DISPATCHED) is False

    def test_order_transitions_from_dispatched(self):
        order = OrderFactory(status=Order.Status.DISPATCHED)
        assert order.can_transition_to(Order.Status.DELIVERED) is True
        assert order.can_transition_to(Order.Status.CANCELLED) is False

    def test_delivered_has_no_transitions(self):
        order = OrderFactory(status=Order.Status.DELIVERED)
        assert order.get_allowed_transitions() == []

    def test_cancelled_has_no_transitions(self):
        order = OrderFactory(status=Order.Status.CANCELLED)
        assert order.get_allowed_transitions() == []

    def test_item_count(self):
        order = OrderFactory()
        OrderItemFactory(order=order, quantity=3)
        OrderItemFactory(order=order, quantity=2)
        assert order.item_count == 5

    def test_total_weight_kg(self):
        order = OrderFactory()
        p1 = ProductFactory(weight_kg=Decimal("1.000"))
        p2 = ProductFactory(weight_kg=Decimal("0.500"))
        OrderItemFactory(order=order, product=p1, quantity=2)
        OrderItemFactory(order=order, product=p2, quantity=1)
        assert order.total_weight_kg == pytest.approx(2.5)

    def test_status_badge_class_exists_for_all_statuses(self):
        for status, _ in Order.Status.choices:
            order = OrderFactory(status=status)
            badge = order.status_badge_class
            assert "bg-" in badge


class TestOrderItemModel:
    def test_total_weight(self):
        product = ProductFactory(weight_kg=Decimal("2.500"))
        item = OrderItemFactory(product=product, quantity=3)
        assert item.total_weight_kg == pytest.approx(7.5)

    def test_str_representation(self):
        product = ProductFactory(name="Widget")
        item = OrderItemFactory(product=product, quantity=2)
        assert "2" in str(item)
        assert "Widget" in str(item)