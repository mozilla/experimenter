from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models


class Prefs(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="glean_prefs"
    )
    alert_dismissed = models.BooleanField(default=False)
    opt_out = models.BooleanField(default=False)
    nimbus_user_id = models.UUIDField(
        default=uuid4, editable=False, null=True, unique=True
    )

    class Meta:
        verbose_name = "glean prefs"
        verbose_name_plural = "glean prefs"

    def __str__(self):
        return (
            f"Prefs(user={self.user},alert_dismissed={self.alert_dismissed}"
            f",opt_out={self.opt_out},nimbus_user_id={self.nimbus_user_id})"
        )

    def save(self, *args, **kwargs):
        if self.nimbus_user_id is not None and self.opt_out:
            self.nimbus_user_id = None
        if self.nimbus_user_id is None and not self.opt_out:
            self.nimbus_user_id = uuid4()
        super().save(*args, **kwargs)
