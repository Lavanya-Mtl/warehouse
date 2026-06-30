from django.db import models


class Box(models.Model):
    name = models.CharField(max_length=100)
    # Internal dimensions in centimetres
    internal_length_cm = models.DecimalField(max_digits=8, decimal_places=2)
    internal_width_cm = models.DecimalField(max_digits=8, decimal_places=2)
    internal_height_cm = models.DecimalField(max_digits=8, decimal_places=2)
    # Max weight it can hold in kilograms
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    # Cost in pence/cents (store as integer to avoid float issues)
    cost_rupees = models.PositiveIntegerField(help_text="Cost in rupees (e.g. 150 = INR 150)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cost_rupees"]

    def __str__(self):
        return (
            f"{self.name} "
            f"({self.internal_length_cm}×{self.internal_width_cm}×{self.internal_height_cm} cm, "
            f"max {self.max_weight_kg} kg)"
        )

    @property
    def cost_display(self):
        return f"INR {self.cost_rupees:.2f}"

    @property
    def volume_cm3(self):
        return (
            float(self.internal_length_cm)
            * float(self.internal_width_cm)
            * float(self.internal_height_cm)
        )