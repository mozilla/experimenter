# Pre-Launch Population Sizing: Proposal

## Background

Experimenter currently fetches a pre-computed, globally-aggregated sizing dataset from GCS once per week (Monday 06:00 UTC via `fetch_population_sizing_data`). That dataset is keyed by `app_id / SizingUserType / channel / country` and reports `number_of_clients_targeted`, `sample_size_per_branch`, and `population_percent_per_branch` for a handful of canonical targeting recipes. The data is stored in Redis under `SIZING_DATA_KEY` but is not yet surfaced in any Experimenter view or API response.

The goal of this proposal is to extend that foundation with:

1. A per-experiment estimated eligible population count, derived from the experiment's JEXL targeting expression.
2. Validation of JEXL-to-SQL translations against real SDK enrollment decisions via `enrollment_status` telemetry.

---

## How enrollment_status Helps Pre-Launch Sizing

### Status: enrollment_status is ON BY DEFAULT (no gating)

As of the current Firefox Desktop release cycle, the `enrollment_status` Glean event (`nimbus_events / enrollment_status`) is **enabled for all Firefox Desktop clients by default**. The earlier feature-flag gate (`enable-enrollment-status-telemetry-for-firefox-desktop-via-nimbustelemetry`) has been removed. There is no longer a gated sub-population — every eligible Desktop client fires this event on every Nimbus evaluation cycle.

This has two important consequences for pre-launch sizing:

#### 1. Full-population JEXL validation (before launch)

Because `enrollment_status` fires for all clients (both `Enrolled` and `NotEnrolled`), the `NotEnrolled` rows tell us, for any live or paused experiment, exactly how many clients the SDK evaluated against the targeting JEXL and decided were not eligible. This gives us a ground-truth reference against which to compare our JEXL-to-SQL estimates.

Workflow:
```
Write JEXL → Translate to SQL → Run SQL on nimbus_targeting_context → Compare count
                                                                         against enrollment_status
                                                                         NotEnrolled/Enrolled split
```

If the SQL count matches the enrollment_status eligible count (within a few percent), the translation is correct.

#### 2. Historical sizing for re-run experiments

If an experiment with identical or nearly identical targeting has been run before, its `enrollment_status` history in BigQuery gives a direct empirical estimate of the eligible population — no SQL translation needed. This is the highest-confidence sizing signal available.

### What enrollment_status provides

| Field | BigQuery location |
|---|---|
| Event category | `e.category = 'nimbus_events'` |
| Event name | `e.name = 'enrollment_status'` |
| Experiment slug | `e.extra.experiment` (or `e.extra.slug`) |
| Status | `e.extra.status` — `Enrolled`, `NotEnrolled`, `WasEnrolled`, `Disqualified`, `ErrorEnrolling` |
| Branch | `e.extra.branch` |
| Reason | `e.extra.reason` |

The relevant table is `mozdata.firefox_desktop.nimbus_events` (Glean events ping). For population sizing the most useful statuses are `Enrolled` and `NotEnrolled`; the ratio `Enrolled / (Enrolled + NotEnrolled)` is the targeting hit rate.

### Updated "Gotchas" section

**Previously documented gotcha (now historical):**

> enrollment_status data is only available for the sub-population that has the
> `enable-enrollment-status-telemetry-for-firefox-desktop-via-nimbustelemetry`
> Nimbus feature enabled — do not treat it as fully representative.

**Current status:** This gate has been removed. `enrollment_status` is representative of the full Firefox Desktop population and can be used without any population-coverage correction.

---

## Corrected SQL Template: nimbus_targeting_context

The SQL template for estimating the eligible population from `nimbus_targeting_context` had several column-name and logic bugs. The corrected version is maintained at:

```
experimenter/experimenter/experiments/sql/pre_launch_population_sizing_desktop.sql
```

Key fixes:

| Bug | Wrong | Correct |
|---|---|---|
| Table | `moz-fx-data-shared-prod.firefox_desktop.metrics` | `mozdata.firefox_desktop.nimbus_targeting_context` |
| Channel column | `nimbus_targeting_context_update_channel` | `JSON_VALUE(metrics.object.nimbus_targeting_context_browser_settings, '$.update.channel')` |
| Profile age column | `nimbus_targeting_context_profile_age_in_days` | Derived via `DATE_DIFF` from `profile_age_created` (stored as epoch milliseconds INT64) |
| Windows OS detection | `JSON_VALUE(..., '$.isWindows')` | `NOT JSON_VALUE(..., '$.isMac') = 'true' AND NOT JSON_VALUE(..., '$.isLinux') = 'true'` |
| client_id | top-level `client_id` | `client_info.client_id` |

---

## Validation Query: enrollment_status vs. SQL estimate

See the validation query section at the bottom of `pre_launch_population_sizing_desktop.sql` for a ready-to-run template that compares the JEXL-to-SQL count against the observed `enrollment_status` counts for a named experiment.

---

## Implementation Plan (Phased)

### Phase 1: Expose existing GCS data in the Experimenter API (already computed, not yet surfaced)

- Add a GraphQL field `populationSizing` to the `NimbusExperimentType` that reads from `cache.get(settings.SIZING_DATA_KEY)` and matches on `app_id` + `channel` + `country`.
- Render the matched `number_of_clients_targeted` on the Audience tab in the UI.

### Phase 2: Per-experiment JEXL-to-SQL estimates (new)

- Implement a `jexl_to_sql` converter for the subset of JEXL constructs used in Nimbus targeting (version comparisons, locale/country string matches, OS booleans, profile age).
- Run the corrected SQL template against `mozdata.firefox_desktop.nimbus_targeting_context` with the translated WHERE clause.
- Store the result as `estimated_eligible` on `NimbusExperiment` (or in the GCS output file).
- Schedule via a new Celery task running daily, limited to experiments in Draft/Preview/Review status.

### Phase 3: enrollment_status validation (new)

- For any experiment that has previously run (status Complete) or is currently live, compare the Phase 2 SQL estimate against the observed `enrollment_status` counts.
- Surface the comparison in the Experimenter UI as a confidence indicator for the estimate.

---

## Open Questions

1. Should `estimated_eligible` be re-computed on every recipe change, or only on-demand?
2. What JEXL constructs are out of scope for the SQL translator (e.g. `regExpMatch`, nested `||` on non-primitive fields)?
3. For mobile apps (Fenix, iOS), `nimbus_targeting_context` is not available — what is the equivalent table?
