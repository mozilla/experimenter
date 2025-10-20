from django.db import models


class FeatureTestRun(models.Model):
    """Track QA test runs for a specific feature independent of experiments.

    This model tracks when features are tested, how complex the changes were,
    and links to relevant documentation. It references NimbusFeatureConfig
    which contains the feature slug and application information.
    """

    feature_config = models.ForeignKey(
        "experiments.NimbusFeatureConfig",
        related_name="test_runs",
        on_delete=models.CASCADE,
        null=False,
    )
    change_link = models.URLField(
        max_length=2000,
        null=True,
        blank=True,
    )
    change_date = models.DateTimeField(null=False)
    change_size = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    complexity = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("LOW", "Low"),
            ("MEDIUM", "Medium"),
            ("HIGH", "High"),
        ],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feature Test Run"
        verbose_name_plural = "Feature Test Runs"
        ordering = ["-change_date"]
        indexes = [
            models.Index(fields=["feature_config", "-change_date"]),
        ]

    def __str__(self):
        return f"{self.feature_config} - {self.change_date.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def get_for_feature(cls, feature_config):
        """Get all test runs for a specific feature config."""
        return cls.objects.filter(feature_config=feature_config)

    @classmethod
    def get_last_tested(cls, feature_config):
        """Get the most recent test run for a feature config."""
        return cls.objects.filter(feature_config=feature_config).first()

    @classmethod
    def get_test_count(cls, feature_config):
        """Get the count of test runs for a feature config."""
        return cls.objects.filter(feature_config=feature_config).count()

"""
from experimenter.features.models import FeatureTestRun
from experimenter.features import Features
from django.utils import timezone
test_run = FeatureTestRun.objects.create(
    application="firefox-desktop",
    slug="no-feature-firefox-desktop",
    change_date=timezone.datetime.now(),
    complexity="MEDIUM",
    change_size="300",
    )
"""
