from django.contrib.auth import get_user_model
from django.db import models


class NotificationManager(models.Manager):
    @property
    def has_unread(self):
        return self.filter(read=False).count() > 0

    def get_unread(self):
        unread = list(self.filter(read=False))

        self.update(read=True)

        return unread


class Notification(models.Model):

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="notifications"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    read = models.BooleanField(default=False)

    objects = NotificationManager()

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ("created_on",)

    def __str__(self):  # pragma: no cover
        return self.message
