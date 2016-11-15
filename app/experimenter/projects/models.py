from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    slug = models.SlugField(
        max_length=255, unique=True, blank=False, null=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
