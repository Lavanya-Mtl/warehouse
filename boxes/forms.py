from django import forms
from .models import Box


class BoxForm(forms.ModelForm):
    class Meta:
        model = Box
        fields = [
            "name",
            "internal_length_cm",
            "internal_width_cm",
            "internal_height_cm",
            "max_weight_kg",
            "cost_rupees",
            "is_active",
        ]
        help_texts = {
            "cost_rupees": "Enter cost in pence. E.g. 150 for £1.50",
        }