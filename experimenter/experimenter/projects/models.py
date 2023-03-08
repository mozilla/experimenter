from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name
