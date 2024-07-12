# forms.py

from django import forms

from experimenter.experiments.models import NimbusExperiment


class QAStatusForm(forms.ModelForm):
    class Meta:
        model = NimbusExperiment
        fields = ["qa_status", "qa_comment"]
        widgets = {
            "qa_status": forms.Select(choices=NimbusExperiment.QAStatus),
        }


class TakeawaysForm(forms.ModelForm):
    conclusion_recommendations = forms.MultipleChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = NimbusExperiment
        fields = [
            "takeaways_metric_gain",
            "takeaways_gain_amount",
            "takeaways_qbr_learning",
            "takeaways_summary",
            "conclusion_recommendations",
        ]
        widgets = {
            "takeaways_gain_amount": forms.Textarea(
                attrs={
                    "placeholder": "Examples: 0.5% gain in retention, \
                        or 0.5% gain in days of use",
                    "rows": 5,
                }
            ),
        }
