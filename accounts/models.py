from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        WAREHOUSE_STAFF = "staff", "Warehouse Staff"
        MANAGER = "manager", "Manager"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WAREHOUSE_STAFF,
    )

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"