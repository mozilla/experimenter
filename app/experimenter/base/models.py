from django.db import models


class SiteFlagNameChoices(models.TextChoices):
    LAUNCHING_DISABLED = "LAUNCHING_DISABLED", "Disable launching experiments"


class SiteFlagManager(models.Manager):
    def value(self, choice, defval=False):
        qs = self.get_queryset().filter(name=choice.name)
        if qs.exists():
            return qs.get().value
        return defval


class SiteFlag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    value = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    objects = SiteFlagManager()

    @property
    def description(self):
        if self.name in SiteFlagNameChoices:
            return SiteFlagNameChoices[self.name].label
        return self.name

    def __str__(self):
        return f"{self.description}: {self.value}"


class Locale(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)
        verbose_name = "Locale"
        verbose_name_plural = "Locales"

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.code}>"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Country(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.code}>"

    def __str__(self):
        return f"{self.name} ({self.code})"
