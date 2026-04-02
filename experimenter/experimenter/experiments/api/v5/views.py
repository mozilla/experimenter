import csv
import datetime
import io
from collections import defaultdict

import yaml
from dateutil.relativedelta import relativedelta
from django.db.models import F
from django.http import HttpResponse
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.cache import CachedListMixin
from experimenter.experiments.api.v5.serializers import (
    FmlFeatureValueSerializer,
    NimbusExperimentCsvSerializer,
    NimbusExperimentYamlSerializer,
)
from experimenter.experiments.models import NimbusChangeLog, NimbusExperiment


class NimbusExperimentCsvRenderer(CSVRenderer):
    header = NimbusExperimentCsvSerializer.Meta.fields
    labels = {field: field.replace("_", " ").title() for field in header}


class NimbusExperimentCsvListView(CachedListMixin, ListAPIView):
    cache_key_prefix = "v5:csv"
    cache_content_type = "text/csv; charset=utf-8"
    queryset = (
        NimbusExperiment.objects.select_related("owner")
        .prefetch_related("feature_configs")
        .filter(is_archived=False)
    )
    serializer_class = NimbusExperimentCsvSerializer
    renderer_classes = (NimbusExperimentCsvRenderer,)

    def get_queryset(self):
        return sorted(
            super().get_queryset(),
            key=lambda experiment: (
                (experiment.start_date and experiment.start_date.strftime("%Y-%m-%d"))
                or ""
            ),
            reverse=True,
        )


class NimbusExperimentUsageStatsView(APIView):
    NOVICE_MAX = 3
    INTERMEDIATE_MAX = 9

    @staticmethod
    def _generate_usage_csv():
        experiments = (
            NimbusExperiment.objects.filter(
                _start_date__isnull=False,
                status=NimbusExperiment.Status.COMPLETE,
            )
            .values_list("owner__email", "_start_date")
            .order_by("_start_date")
        )
        approvals = (
            NimbusChangeLog.objects.filter(
                old_publish_status=NimbusExperiment.PublishStatus.REVIEW,
                new_publish_status=NimbusExperiment.PublishStatus.APPROVED,
                experiment___start_date__isnull=False,
            )
            .values_list("changed_by__email", "experiment___start_date")
            .order_by("experiment___start_date")
        )

        owner_events = defaultdict(list)
        for email, start_date in experiments:
            owner_events[start_date.strftime("%Y-%m")].append(email)

        reviewer_events = defaultdict(set)
        for email, start_date in approvals:
            reviewer_events[start_date.strftime("%Y-%m")].add(email)

        if not owner_events and not reviewer_events:
            return ""

        last_month = max(set(owner_events) | set(reviewer_events))
        end_date = datetime.datetime.strptime(last_month, "%Y-%m").date()

        seen_owners = set()
        seen_reviewers = set()
        counts = defaultdict(int)
        rows = []
        current = datetime.date(2020, 1, 1)
        novice_max = NimbusExperimentUsageStatsView.NOVICE_MAX
        intermediate_max = NimbusExperimentUsageStatsView.INTERMEDIATE_MAX
        while current <= end_date:
            month = current.strftime("%Y-%m")
            for email in owner_events.get(month, []):
                seen_owners.add(email)
                counts[email] += 1
            seen_reviewers |= reviewer_events.get(month, set())

            experience_levels = [0, 0, 0]
            for count in counts.values():
                experience_levels[
                    0 if count <= novice_max else 1 if count <= intermediate_max else 2
                ] += 1

            rows.append(
                [month, len(seen_owners), len(seen_reviewers), *experience_levels]
            )
            current += relativedelta(months=1)

        output = io.StringIO()
        header = [
            "Month",
            "Owners",
            "Reviewers",
            f"Novice (0-{novice_max})",
            f"Intermediate ({novice_max + 1}-{intermediate_max})",
            f"Advanced ({intermediate_max + 1}+)",
        ]
        writer = csv.writer(output)
        writer.writerow(header)
        quarter_ends = {}
        for row in rows:
            writer.writerow(row)
            row_date = datetime.datetime.strptime(row[0], "%Y-%m").date()
            quarter = f"{row_date.year} Q{(row_date.month - 1) // 3 + 1}"
            quarter_ends[quarter] = row

        writer.writerow([])
        for quarter in sorted(quarter_ends):
            writer.writerow([quarter, *quarter_ends[quarter][1:]])

        return output.getvalue()

    def get(self, request):
        csv_content = self._generate_usage_csv()
        return HttpResponse(csv_content, content_type="text/csv; charset=utf-8")


class NimbusExperimentYamlRenderer(BaseRenderer):
    media_type = "text/yaml"
    format = "yaml"
    charset = "utf-8"

    @staticmethod
    def _strip_empty(obj):
        if isinstance(obj, dict):
            return {
                k: NimbusExperimentYamlRenderer._strip_empty(v)
                for k, v in obj.items()
                if v is not None and v != "" and v != [] and v != {}
            }
        if isinstance(obj, list):
            return [NimbusExperimentYamlRenderer._strip_empty(i) for i in obj]
        return obj

    def render(self, data, accepted_media_type=None, renderer_context=None):
        experiments = [self._strip_empty(exp) for exp in data["results"]]
        output = {
            **{k: v for k, v in data.items() if k != "results"},
            "experiments": experiments,
        }
        return yaml.dump(
            output,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


class YamlExportPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = None
    max_page_size = 100


class NimbusExperimentYamlListView(CachedListMixin, ListAPIView):
    cache_key_prefix = "v5:yaml"
    cache_content_type = "text/yaml; charset=utf-8"
    queryset = (
        NimbusExperiment.objects.select_related("owner", "reference_branch", "parent")
        .prefetch_related(
            "feature_configs",
            "branches",
            "branches__feature_values__feature_config",
            "documentation_links",
            "projects",
            "locales",
            "countries",
            "languages",
            "tags",
            "required_experiments",
            "excluded_experiments",
        )
        .filter(is_archived=False, status=NimbusExperiment.Status.COMPLETE)
        .order_by(F("_start_date").desc(nulls_last=True), "-id")
    )
    serializer_class = NimbusExperimentYamlSerializer
    renderer_classes = (NimbusExperimentYamlRenderer,)
    pagination_class = YamlExportPagination


class FmlErrorsView(UpdateAPIView):
    queryset = NimbusExperiment.objects.all()
    lookup_field = "slug"
    serializer_class = FmlFeatureValueSerializer
