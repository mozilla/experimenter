from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)
    dashboard_url = models.URLField(blank=True, null=True)
    dashboard_image_url = models.URLField(blank=True, null=True)
    image = models.FileField(upload_to='projects/', blank=True, null=True)

    def __str__(self):  # pragma: no cover
        return self.name

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
