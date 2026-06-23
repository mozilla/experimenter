from dataclasses import dataclass, field

from scipy.stats import chisquare

from experimenter.experiments.constants import NimbusConstants


@dataclass
class FeatureConflictResult:
    is_conflict: bool
    rate: float
    slugs: list[str] = field(default_factory=list)


UNENROLLMENT_SPIKE_THRESHOLD = 0.10
SRM_MISMATCH_P_VALUE_THRESHOLD = 0.001
SRM_MISMATCH_MIN_RATIO_DEVIATION = 0.05


def compute_unenrollment_rate(total_enrollments, total_unenrollments):
    if total_enrollments == 0:
        return 0.0
    return total_unenrollments / total_enrollments


def compute_srm_p_value(branches, branch_ratios):
    branch_names = list(branches.keys())
    enrollments = [branches[b].get("enrollments", 0) for b in branch_names]

    if not enrollments or sum(enrollments) == 0:
        return 1.0

    total = sum(enrollments)

    if branch_ratios and all(b in branch_ratios for b in branch_names):
        total_ratio = sum(branch_ratios[b] for b in branch_names) or 1
        expected = [total * branch_ratios[b] / total_ratio for b in branch_names]
    else:
        expected_per_branch = total / len(enrollments)
        expected = [expected_per_branch] * len(enrollments)

    _, p_value = chisquare(enrollments, expected)
    return p_value


def get_top_unenrollment_reason(monitoring_data):
    reasons_by_branch = monitoring_data.get("reasons_by_branch", {})

    if not reasons_by_branch:
        return "unknown"

    aggregated_reasons = {}
    for branch_reasons in reasons_by_branch.values():
        for reason, count_data in branch_reasons.items():
            count = count_data.get("1pct_count", 0)
            aggregated_reasons[reason] = aggregated_reasons.get(reason, 0) + count

    if not aggregated_reasons:
        return "unknown"

    return max(aggregated_reasons, key=aggregated_reasons.get)


def check_unenrollment_spike(monitoring_data):
    rate = compute_unenrollment_rate(
        monitoring_data.get("total_enrollments", 0),
        monitoring_data.get("total_unenrollments", 0),
    )
    return rate > UNENROLLMENT_SPIKE_THRESHOLD, rate


def compute_max_ratio_deviation(branches, branch_ratios):
    branch_names = list(branches.keys())
    enrollments = [branches[b].get("enrollments", 0) for b in branch_names]
    total = sum(enrollments)
    if total == 0 or len(enrollments) < 2:
        return 0.0

    if branch_ratios and all(b in branch_ratios for b in branch_names):
        total_ratio = sum(branch_ratios[b] for b in branch_names) or 1
        expected_ratios = [branch_ratios[b] / total_ratio for b in branch_names]
    else:
        expected_ratios = [1.0 / len(enrollments)] * len(enrollments)

    actual_ratios = [e / total for e in enrollments]
    return max(abs(a - e) for a, e in zip(actual_ratios, expected_ratios))


def check_srm_mismatch(monitoring_data, branch_ratios):
    branches = monitoring_data.get("branches", {})

    if len(branches) < 2:
        return False, 1.0

    p_value = compute_srm_p_value(branches, branch_ratios)
    max_deviation = compute_max_ratio_deviation(branches, branch_ratios)

    is_srm = (
        p_value < SRM_MISMATCH_P_VALUE_THRESHOLD
        and max_deviation >= SRM_MISMATCH_MIN_RATIO_DEVIATION
    )
    return is_srm, p_value


def check_zero_enrollment(
    monitoring_data, days_since_start, threshold_days, client_threshold
):
    if days_since_start < threshold_days:
        return False

    total_enrollments = monitoring_data.get("total_enrollments", 0)
    return total_enrollments < client_threshold


def check_feature_conflict(monitoring_data, threshold):
    funnel = monitoring_data.get("enrollment_funnel", [])
    if not funnel:
        return FeatureConflictResult(is_conflict=False, rate=0.0, slugs=[])

    total = sum(row.get("client_count", 0) for row in funnel)
    if total == 0:
        return FeatureConflictResult(is_conflict=False, rate=0.0, slugs=[])

    conflict_count = 0
    conflict_slugs = set()

    for row in funnel:
        if row.get("reason") == NimbusConstants.FunnelReason.FEATURE_CONFLICT:
            conflict_count += row.get("client_count", 0)
            slug = row.get("conflict_slug")
            if slug:
                conflict_slugs.add(slug)

    rate = conflict_count / total
    return FeatureConflictResult(
        is_conflict=rate >= threshold,
        rate=rate,
        slugs=sorted(conflict_slugs),
    )
