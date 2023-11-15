import json
import logging
from typing import Any, Dict, List

from cirrus_sdk import (  # type: ignore
    CirrusClient,
    EnrollmentStatusExtraDef,
    MetricsHandler,
    NimbusError,
)

logger = logging.getLogger(__name__)


class CirrusMetricsHandler(MetricsHandler):
    def __init__(self, metrics: Any, pings: Any):
        self.metrics = metrics
        self.pings = pings

    def record_enrollment_statuses(
        self, enrollment_status_extras: list[EnrollmentStatusExtraDef]
    ):
        for enrollment_status_extra in enrollment_status_extras:
            self.metrics.cirrus_events.enrollment_status.record(
                self.metrics.cirrus_events.EnrollmentStatusExtra(
                    branch=enrollment_status_extra.branch or "",
                    conflict_slug=enrollment_status_extra.conflict_slug or "",
                    error_string=enrollment_status_extra.error_string or "",
                    reason=enrollment_status_extra.reason or "",
                    slug=enrollment_status_extra.slug or "",
                    status=enrollment_status_extra.status or "",
                    user_id=enrollment_status_extra.user_id or "",
                )
            )
        self.pings.enrollment_status.submit()


class SDK:
    def __init__(
        self,
        context: str,
        coenrolling_feature_ids: List[str],
        metrics_handler: CirrusMetricsHandler,
    ):
        self.client = CirrusClient(context, metrics_handler, coenrolling_feature_ids)

    def compute_enrollments(self, targeting_context: Dict[str, str]) -> Dict[str, Any]:
        try:
            res = self.client.handle_enrollment(json.dumps(targeting_context))
            return json.loads(res)
        except (NimbusError, Exception) as e:  # type: ignore
            logger.error(f"An error occurred during compute_enrollments: {e}")
            return {}

    def set_experiments(self, recipes: str):
        try:
            self.client.set_experiments(recipes)
        except NimbusError as e:  # type: ignore
            logger.error(f"An error occurred during set_experiments: {e}")
