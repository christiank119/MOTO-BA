from django import forms
from .models import RaumPlan

class RaumPlanForm(forms.ModelForm):
    class Meta:
        model = RaumPlan
        fields = ['title', 'image', 'width', 'height']
