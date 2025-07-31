from django.contrib.auth.models import User
from django.db import models


class Prefs(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="glean_prefs"
    )
    alert_dismissed = models.BooleanField(default=False)
    opt_out = models.BooleanField(default=False)

    class Meta:
        verbose_name = "glean prefs"
        verbose_name_plural = "glean prefs"

    def __str__(self):
        return (
            f"Prefs(user={self.user},alert_dismissed={self.alert_dismissed}"
            f",opt_out={self.opt_out})"
        )
