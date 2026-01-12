import json
import logging
from typing import Any

from cirrus_sdk import (  # type: ignore
    CirrusClient,
    EnrollmentStatusExtraDef,
    MetricsHandler,
    NimbusError,
)

logger = logging.getLogger(__name__)


class CirrusMetricsHandler(MetricsHandler):
    def __init__(self, enrollment_status_ping: Any):
        self.enrollment_status_ping = enrollment_status_ping

    def record_enrollment_statuses(
        self, enrollment_status_extras: list[EnrollmentStatusExtraDef]
    ):
        self.record_enrollment_statuses_v2(
            enrollment_status_extras=enrollment_status_extras,
            nimbus_user_id=(
                enrollment_status_extras[0].user_id if enrollment_status_extras else None
            ),
        )

    def record_enrollment_statuses_v2(
        self,
        enrollment_status_extras: list[EnrollmentStatusExtraDef],
        nimbus_user_id: str | None,
    ):
        self.enrollment_status_ping.record(
            user_agent=None,
            ip_address=None,
            nimbus_nimbus_user_id=nimbus_user_id or "",
            events=[
                {
                    "category": "cirrus_events",
                    "name": "enrollment_status",
                    "extra": {
                        "branch": str(enrollment_status_extra.branch or ""),
                        "conflict_slug": str(enrollment_status_extra.conflict_slug or ""),
                        "error_string": str(enrollment_status_extra.error_string or ""),
                        "reason": str(enrollment_status_extra.reason or ""),
                        "slug": str(enrollment_status_extra.slug or ""),
                        "status": str(enrollment_status_extra.status or ""),
                        "nimbus_user_id": str(enrollment_status_extra.user_id or ""),
                    },
                }
                for enrollment_status_extra in enrollment_status_extras
            ],
        )


class SDK:
    def __init__(
        self,
        context: str,
        coenrolling_feature_ids: list[str],
        metrics_handler: CirrusMetricsHandler,
    ):
        self.client = CirrusClient(context, metrics_handler, coenrolling_feature_ids)

    def compute_enrollments(self, targeting_context: dict[str, str]) -> dict[str, Any]:
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
