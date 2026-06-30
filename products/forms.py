from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "length_cm", "width_cm", "height_cm", "weight_kg", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }