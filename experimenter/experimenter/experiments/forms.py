# forms.py

from django import forms
from .models import NimbusExperiment


class QAStatusForm(forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["qa_status"]
        widgets = {
            "qa_status": forms.Select(choices=NimbusExperiment.QAStatus),
        }
