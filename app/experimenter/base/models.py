from django.db import models


class Locale(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)
        verbose_name = "Locale"
        verbose_name_plural = "Locales"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Country(models.Model):
    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
