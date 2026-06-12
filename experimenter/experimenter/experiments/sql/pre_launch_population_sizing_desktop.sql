-- Pre-launch population sizing for Firefox Desktop
--
-- Estimates the number of clients that would match a given set of targeting
-- criteria BEFORE the experiment launches, using the daily
-- mozdata.firefox_desktop.nimbus_targeting_context table.
--
-- Table facts (confirmed from live BQ schema):
--   client_id:            client_info.client_id  (nested)
--   sample_id:            top-level INT64 (0-99)
--   partition:            submission_timestamp  (use DATE(submission_timestamp))
--   channel:              JSON_VALUE(metrics.object.nimbus_targeting_context_browser_settings, '$.update.channel')
--   locale:               metrics.string.nimbus_targeting_context_locale
--   profile_age_created:  metrics.quantity.nimbus_targeting_context_profile_age_created  (epoch ms INT64)
--   os JSON:              metrics.object.nimbus_targeting_context_os
--                           keys: isMac, isLinux, windowsBuildNumber, windowsVersion
--                           NO isWindows key — derive as: NOT isMac AND NOT isLinux
--
-- Usage:
--   Set the DECLARE variables below to match the experiment's targeting,
--   then run. Output: eligible_clients_sample, eligible_clients_full (x10), pct_of_dau.

DECLARE param_channel STRING DEFAULT 'release';
DECLARE param_min_profile_age_days INT64 DEFAULT 0;
DECLARE param_windows_only BOOL DEFAULT FALSE;
DECLARE param_country STRING DEFAULT NULL;        -- NULL = all countries
DECLARE param_locale_prefix STRING DEFAULT NULL;  -- e.g. 'en' matches 'en-US','en-GB'. NULL = all
DECLARE param_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

WITH base AS (
  SELECT
    client_info.client_id                                                         AS client_id,

    -- Channel: from browserSettings JSON object (no flat column exists)
    JSON_VALUE(
      metrics.object.nimbus_targeting_context_browser_settings, '$.update.channel'
    )                                                                             AS channel,

    -- OS detection: $.isWindows does not exist in the JSON
    -- Windows = NOT isMac AND NOT isLinux
    JSON_VALUE(metrics.object.nimbus_targeting_context_os, '$.isMac')            AS os_is_mac,
    JSON_VALUE(metrics.object.nimbus_targeting_context_os, '$.isLinux')          AS os_is_linux,

    -- Profile age: epoch ms INT64, convert to days
    DATE_DIFF(
      CURRENT_DATE(),
      DATE(TIMESTAMP_MILLIS(
        CAST(metrics.quantity.nimbus_targeting_context_profile_age_created AS INT64)
      )),
      DAY
    )                                                                             AS profile_age_days,

    -- Locale: flat string column
    metrics.string.nimbus_targeting_context_locale                               AS locale,

    -- Country from Glean geo enrichment
    normalized_country_code                                                       AS country

  FROM `mozdata.firefox_desktop.nimbus_targeting_context`
  WHERE DATE(submission_timestamp) = param_date
    AND sample_id < 10  -- 10% sample; multiply final counts by 10
),

filtered AS (
  SELECT client_id
  FROM base
  WHERE
    channel = param_channel

    AND profile_age_days >= param_min_profile_age_days

    -- Windows: NOT isMac AND NOT isLinux
    AND (
      NOT param_windows_only
      OR (
        COALESCE(os_is_mac,   'false') != 'true'
        AND COALESCE(os_is_linux, 'false') != 'true'
      )
    )

    AND (param_country IS NULL OR country = param_country)

    AND (
      param_locale_prefix IS NULL
      OR STARTS_WITH(LOWER(locale), LOWER(param_locale_prefix))
    )

  GROUP BY client_id  -- deduplicate to one row per client
),

channel_dau AS (
  SELECT COUNT(DISTINCT client_info.client_id) AS total_channel_sample
  FROM `mozdata.firefox_desktop.nimbus_targeting_context`
  WHERE DATE(submission_timestamp) = param_date
    AND sample_id < 10
    AND JSON_VALUE(
      metrics.object.nimbus_targeting_context_browser_settings, '$.update.channel'
    ) = param_channel
)

SELECT
  COUNT(f.client_id)                                    AS eligible_clients_sample,
  COUNT(f.client_id) * 10                               AS eligible_clients_full,
  ROUND(
    SAFE_DIVIDE(COUNT(f.client_id), ANY_VALUE(dau.total_channel_sample)),
    4
  )                                                     AS pct_of_channel_dau,
  param_date                                            AS sizing_date,
  param_channel                                         AS channel,
  param_country                                         AS country,
  param_locale_prefix                                   AS locale_prefix,
  param_min_profile_age_days                            AS min_profile_age_days,
  param_windows_only                                    AS windows_only

FROM filtered f
CROSS JOIN channel_dau dau;


-- =============================================================================
-- VALIDATION QUERY: Compare SQL estimate vs. enrollment_status ground truth
--
-- enrollment_status is ON BY DEFAULT for all Firefox Desktop clients as of 2026.
-- The old gating rollout (enable-enrollment-status-telemetry-for-firefox-desktop-
-- via-nimbustelemetry) has been removed. Counts are fully representative.
--
-- Run this after the sizing query above for an experiment with similar targeting.
-- If agreement_pct is within ±10%, the JEXL→SQL translation is correct.
-- =============================================================================

DECLARE experiment_slug STRING DEFAULT 'your-experiment-slug-here';
DECLARE validation_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

WITH sdk_counts AS (
  SELECT
    (SELECT value FROM UNNEST(e.extra) WHERE key = 'status') AS status,
    COUNT(DISTINCT client_info.client_id)                     AS clients
  FROM `mozdata.firefox_desktop.nimbus_targeting_context`,
    UNNEST(events) AS e
  WHERE DATE(submission_timestamp) = validation_date
    AND sample_id < 10
    AND e.category = 'nimbus_events'
    AND e.name = 'enrollment_status'
    AND (SELECT value FROM UNNEST(e.extra) WHERE key = 'slug') = experiment_slug
  GROUP BY 1
)

SELECT
  SUM(IF(status = 'Enrolled',    clients, 0)) * 10    AS enrolled_sdk,
  SUM(IF(status = 'NotEnrolled', clients, 0)) * 10    AS not_enrolled_sdk,
  SUM(IF(status IN ('Enrolled', 'NotEnrolled'), clients, 0)) * 10  AS eligible_sdk,
  ROUND(SAFE_DIVIDE(
    SUM(IF(status = 'Enrolled', clients, 0)),
    SUM(IF(status IN ('Enrolled', 'NotEnrolled'), clients, 0))
  ), 4)                                               AS hit_rate_sdk,
  -- Compare to eligible_clients_full from the main query:
  -- SAFE_DIVIDE(<eligible_clients_full>, eligible_sdk) AS agreement_pct,
  validation_date,
  experiment_slug
FROM sdk_counts;
