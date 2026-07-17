from django.db import models


class SiteFlagNameChoices(models.TextChoices):
    ADVERTISE_DEVTOOLS = "ADVERTISE_DEVTOOLS", "Advertise nimbus-devtools"


class SiteFlagManager(models.Manager["SiteFlag"]):
    def value(self, choice, defval=False):
        qs = self.get_queryset().filter(name=choice.name)
        return qs.get().value if qs.exists() else defval

    def get_cached(self, request, name):
        if getattr(request, "_cached_site_flags", None) is None:
            request._cached_site_flags = {}

        if name not in request._cached_site_flags:
            site_flag = self.filter(name=name).first()
            request._cached_site_flags[name] = site_flag
        else:
            site_flag = request._cached_site_flags[name]

        return site_flag


class SiteFlag(models.Model):
    name = models.CharField(choices=SiteFlagNameChoices, max_length=255, unique=True)
    value = models.BooleanField()
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    extra_data = models.JSONField(default=None, blank=True, null=True)

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


class Language(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.code}>"

    def __str__(self):
        return f"{self.name} ({self.code})"
