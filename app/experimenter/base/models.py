from django.db import models


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
