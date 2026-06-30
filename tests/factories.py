import factory
from factory.django import DjangoModelFactory
from accounts.models import User
from products.models import Product
from boxes.models import Box
from orders.models import Order, OrderItem
from decimal import Decimal
import random

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    role = User.Role.WAREHOUSE_STAFF


class ManagerFactory(UserFactory):
    role = User.Role.MANAGER


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    sku = factory.Sequence(lambda n: f'PRD-{n:03d}')
    length_cm = factory.LazyFunction(lambda: Decimal(str(round(random.uniform(1, 50), 1))))
    width_cm = factory.LazyFunction(lambda: Decimal(str(round(random.uniform(1, 40), 1))))
    height_cm = factory.LazyFunction(lambda: Decimal(str(round(random.uniform(1, 30), 1))))
    weight_kg = factory.LazyFunction(lambda: Decimal(str(round(random.uniform(1, 20), 2))))
    

class BoxFactory(DjangoModelFactory):
    class Meta:
        model = Box

    name = factory.Sequence(lambda n: f"Box {n}")
    internal_length_cm = 50
    internal_width_cm = 40
    internal_height_cm = 30
    max_weight_kg = 10
    cost_rupees = factory.Sequence(lambda n: 100 + n * 50)
    is_active = True


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    order_number = factory.Sequence(lambda n: f"ORD-{n:05d}")
    customer_name = factory.Faker("name")
    customer_email = factory.Faker("email")
    status = Order.Status.PENDING
    created_by = factory.SubFactory(UserFactory)


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1