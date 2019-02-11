from django import forms
from django.utils.text import slugify

from experimenter.projects.models import Project


class NameSlugFormMixin(object):
    """
    Automatically generate a slug from the name field
    """

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)

        if not slug:
            raise forms.ValidationError(
                "This name must include non-punctuation characters."
            )

        return name

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        cleaned_data["slug"] = slugify(name)

        return cleaned_data


class UniqueNameSlugFormMixin(NameSlugFormMixin):
    """
    Automatically generate a slug from the name field
    and ensure that it is unique across all instances
    """

    def clean_name(self):
        name = super().clean_name()
        slug = slugify(name)

        if (
            self.instance.pk is None
            and slug
            and self.Meta.model.objects.filter(slug=slug).exists()
        ):
            raise forms.ValidationError("This name is already in use.")

        return name


class ProjectForm(UniqueNameSlugFormMixin, forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    slug = forms.CharField(required=False)

    class Meta:
        model = Project
        fields = ("name", "slug", "image")
