from django import forms

from experimenter.experiments.models.nimbus import NimbusExperiment


class CreateExperimentForm(forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ("name", "slug", "hypothesis", "public_description")
