from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    # Dimensions in centimetres
    length_cm = models.DecimalField(max_digits=8, decimal_places=2)
    width_cm = models.DecimalField(max_digits=8, decimal_places=2)
    height_cm = models.DecimalField(max_digits=8, decimal_places=2)
    # Weight in kilograms
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def volume_cm3(self):
        return float(self.length_cm) * float(self.width_cm) * float(self.height_cm)