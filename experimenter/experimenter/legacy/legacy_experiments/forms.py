from django import forms


class ExperimentOrderingForm(forms.Form):
    ORDERING_CHOICES = (
        ("-latest_change", "Most Recently Updated"),
        ("latest_change", "Least Recently Updated"),
        ("firefox_min_version", "Firefox Min Version Ascending"),
        ("-firefox_min_version", "Firefox Min Version Descending"),
    )

    ordering = forms.ChoiceField(
        choices=ORDERING_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
