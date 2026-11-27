# nimbus: aggregation-form metric definitions

A metric definition can describe its computation with aggregation fields instead of SQL. Such a
metric names a data source, one aggregation from a closed list, and the columns and conditions that
aggregation reads. Each consumer generates the SQL it needs from the same fields.

The aggregation fields are part of every metric definition that metric-config-parser reads. A
metric declares at most one of `select_expression` or the aggregation fields. A metric that
declares neither stays valid, for example one that only overrides `statistics`, or one that derives
from other metrics with `depends_on`.

`nimbus/` holds metrics in aggregation form, under stricter rules than `definitions/`. Highwind
prefers a metric's copy under `nimbus/`. Jetstream reads `definitions/` only.

Keep aggregation-form metrics under `nimbus/` only for now. metric-config-parser generates
`select_expression` from the aggregation fields, but consumers on older metric-config-parser
releases ignore keys they do not know, so they would read an aggregation-form metric in
`definitions/` as a metric with no SQL.

See [definitions/example_config.toml.example](definitions/example_config.toml.example) for an
annotated example that uses every field.

## Files and layout

`nimbus/` follows the same three-folder convention as `jetstream/`:

```
metric-hub/
  definitions/              metrics with select_expression, and every data source
    firefox_desktop.toml
  nimbus/
    definitions/            one file per application, aggregation form
      firefox_desktop.toml
    defaults/               one file per application: its guardrail metrics
      firefox_desktop.toml
    outcomes/               one folder per application
      firefox_desktop/
        <outcome>.toml      one file per outcome, named after the outcome
```

- `nimbus/definitions/<application>.toml`, `nimbus/defaults/<application>.toml` and
  `nimbus/outcomes/<application>/<outcome>.toml` are the only locations metric-config-parser reads
  under `nimbus/`. Any other path there is ignored.
- All three hold full metric definitions in aggregation form, in the same application namespace.
  Which of the three a metric is declared in is only its default grouping; an application may use
  any or all of them, and none is required to exist.
- The only top-level tables in any of these files are `[metrics]` and `[data_sources]`. Any other
  top-level key is rejected.
- Each metric is a table under `[metrics]`, keyed by the metric name.
- A metric name is declared at most once per application, across all three locations. A metric
  declared more than once is a validation error. See [Validation](#validation).
- A metric may also be defined under the same name in `definitions/<application>.toml`. Highwind
  uses the `nimbus/` copy and Jetstream uses the `definitions/` copy. The two copies must generate
  the same SQL. See [Validation](#validation).
- A metric's `data_source` usually names a data source defined in
  `definitions/<application>.toml`. A data source that exists only inside one of the application's
  Jetstream outcome configs can be referenced directly, with no copy needed in `nimbus/`. A data
  source used only by `nimbus/` metrics can also be declared in any of the application's own files
  under `nimbus/`, under `[data_sources]`. See [Data sources](#data-sources).
- Files ending in `.example` are not loaded.

metric-config-parser loads these files when it loads a repository. `ConfigCollection` returns a
metric from them with `get_nimbus_metric_definition(slug, app_name)`. `get_metric_definition` reads
`definitions/` only.

A consumer on a metric-config-parser release from before `nimbus/defaults/` and
`nimbus/outcomes/` existed does not read either at all, since it never looks there, so adding them
is always safe for it. It still reads `nimbus/definitions/`, and skips a file there it cannot parse
(see [Validation](#validation)).

## Rules for `nimbus/`

- `aggregation` is required. `data_source` is required too, except for a ratio
  (`aggregation = "ratio"`), which takes none; see [Ratios](#ratios).
- `select_expression` is not allowed.
- Only the keys in the field reference below are allowed. Other metric keys accepted in
  `definitions/`, such as `analysis_bases`, `analysis_units`, `type` and `depends_on`, are
  rejected.
- Keys are case sensitive. `definitions/` lowercases keys, `nimbus/` does not.
- `data_source` must name a data source defined in `definitions/<application>.toml`, in one of
  the application's own files under `nimbus/`, or in one of the application's Jetstream outcome
  configs.

## Field reference

The table key is the metric name. The parser does not restrict it beyond TOML key syntax. Use
lowercase snake_case, as in `definitions/`.

Aggregation fields:

| field | type | default | meaning |
| --- | --- | --- | --- |
| `aggregation` | string | | One of `sum`, `sum_where`, `count`, `count_where`, `any`, `recency_within`, `ratio`. Decides how a unit's rows become one value. |
| `column` | string, or a column form | | A column name on the data source, a dotted path to one, or a column form. See [Column forms](#column-forms). |
| `where` | list of conditions | empty | Row conditions for `count_where`, `any` and `sum_where`. |
| `within_days` | integer | | Number of days for `recency_within`, from 1 to 28. |
| `threshold` | `{ op, value }` | | Compares the aggregated value and turns it into 0/1. |
| `scale` | number | | Multiplies the final value. |
| `keep_nulls` | boolean | `false` | Whether a unit with no rows stays null instead of defaulting to 0 (or `FALSE`). Valid only for `sum`, `sum_where` and `any`. See [Keep nulls](#keep-nulls). |
| `encoding` | string | `bits28` | For `recency_within`: `bits28` decodes a 28-day activity bit pattern; `days` means `column` already holds the number of days since the unit was last active. |
| `cumulative_window` | integer (days) | | Length of the cumulative windows Highwind computes. |
| `incremental_window` | integer (days) | | Length of the incremental windows Highwind computes. |
| `repeat_windows` | boolean | `false` | Whether the windows repeat for the length of the experiment. |
| `numerator` | string | | For `ratio` only: the name of a metric declared in `nimbus/` for the same application. See [Ratios](#ratios). |
| `denominator` | string | | For `ratio` only: the name of a metric declared in `nimbus/` for the same application, distinct from `numerator`. See [Ratios](#ratios). |
| `winsorize_quantile` | number | | Highwind-only. The cut point Highwind clips the upper tail at: `0 < q <= 1`. Unset means Highwind's own default. Not valid on a `ratio` or a yes/no metric. See [Winsorization](#winsorization). |
| `winsorize_threshold` | number | | Highwind-only. A fixed upper bound per 7 days that Highwind clips at. Not valid on a `ratio` or a yes/no metric. See [Winsorization](#winsorization). |

Every field other than `aggregation` requires `aggregation`. Which of `column`, `where` and
`within_days` are required depends on the aggregation; `ratio` takes none of them, `numerator` or
`denominator` instead:

| aggregation | `column` | `where` | `within_days` |
| --- | --- | --- | --- |
| `sum` | required | not allowed | not allowed |
| `sum_where` | required | required | not allowed |
| `count` | required | not allowed | not allowed |
| `recency_within` | required | not allowed | required |
| `count_where` | exactly one of `column` or `where` | exactly one of `column` or `where` | not allowed |
| `any` | exactly one of `column` or `where` | exactly one of `column` or `where` | not allowed |

A column name must match `^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$`: one or more
`.`-separated plain names, such as a Glean `metrics.counter.x` or legacy `payload.processes.y`
field path. It is a name, never an expression, so `COALESCE(x, 0)`, `x + 1` and `x > 0` are all
rejected. No aggregation field takes SQL. `column`, and a condition's `column`, may instead be a
column form; see [Column forms](#column-forms).

Other fields allowed in `nimbus/`. These are existing metric fields and are parsed as
they are in `definitions/`:

| field | type | required | default | meaning |
| --- | --- | --- | --- | --- |
| `data_source` | string | yes, except for `ratio` | | Name of a data source defined in `definitions/<application>.toml`, in this file's own `[data_sources]` table, or in one of the application's Jetstream outcome configs. |
| `statistics` | table of tables | no | | Statistics for the metric. |
| `friendly_name` | string | no | | Display name on the results page. |
| `description` | string | no | | Display description on the results page. |
| `bigger_is_better` | boolean | no | `true` | Direction of improvement on the results page. |
| `category` | string | no | | Category used to group metrics. |
| `owner` | string or list of strings | no | | Owner email address or addresses. |
| `deprecated` | boolean | no | `false` | Marks the metric as deprecated. |
| `level` | string | no | | One of `gold`, `silver`, `bronze`. |

## Aggregations

A unit is whatever the analysis counts: a client, or a profile group. Each aggregation reduces a
unit's rows in one window to one value.

### `sum`

The sum of `column` over the unit's rows. Null values are ignored. A unit with no rows, or with only
null values, gets 0 by default; set `keep_nulls = true` to leave it null instead. The result is a
number.

```toml
[metrics.active_hours]
data_source = "clients_daily"
aggregation = "sum"
column = "active_hours_sum"
```

### `sum_where`

The sum of `column` over the unit's rows where every condition holds. A row where a condition
evaluates to null does not match, and contributes nothing to the sum. A unit with rows but no
matching rows gets 0. A unit with no rows at all also gets 0 by default; set `keep_nulls = true`
to leave it null instead. The result is a number. There is no `column` shorthand: both `column`
and `where` are required, since `column` already names the value to sum.

```toml
[metrics.example_sum_where]
data_source = "clients_daily"
aggregation = "sum_where"
column = "example_column"

[[metrics.example_sum_where.where]]
column = "example_condition_column"
op = "="
value = "example_value"
```

### `count`

The number of rows where `column` is not null. A unit with no rows gets 0. The result is a count.

```toml
[metrics.days_of_use]
data_source = "clients_daily"
aggregation = "count"
column = "submission_date"
```

### `count_where`

The number of rows where every condition holds. A row where a condition evaluates to null does not
match. A unit with no rows gets 0. The result is a count.

```toml
[metrics.qualified_cumulative_days_of_use]
data_source = "clients_daily"
aggregation = "count_where"

[[metrics.qualified_cumulative_days_of_use.where]]
column = "active_hours_sum"
op = ">"
value = 0

[[metrics.qualified_cumulative_days_of_use.where]]
column = "scalar_parent_browser_engagement_total_uri_count_normal_and_private_mode_sum"
op = ">"
value = 0
```

### `any`

1 if at least one row matches every condition, otherwise 0. A unit with no rows gets 0 by default;
set `keep_nulls = true` to leave it null instead. The result is 0/1.

```toml
[metrics.is_default_browser]
data_source = "clients_daily"
aggregation = "any"
column = "is_default_browser"
```

### `recency_within`

1 if the unit was active within the last `within_days` days, otherwise 0. `column` must be a
28-day activity bit pattern such as `days_active_bits`, where each row records the days the unit was
active in the 28 days up to and including that row's date.

Each row is decoded to the number of days since the most recent active day, where 0 means active on
the row's own date. The unit's value is the smallest of these over its rows in the window. A unit
with no rows, or with no active days recorded, gets 30, which is outside the 28-day range. The
result is 1 when that value is less than `within_days`, so `within_days = 3` means active on the
row's date or one of the two days before it. `within_days` is at most 28 with either encoding,
because a unit with no rows counts as 30 days since last seen, and a longer window would count it as
active. The result is 0/1.

The decoding, the comparison and the value for a unit with no rows are fixed. The author supplies
only the column and the number of days.

```toml
[metrics.active_in_last_3_days_legacy]
data_source = "firefox_desktop_active_users_view"
aggregation = "recency_within"
column = "days_active_bits"
within_days = 3
```

Set `encoding = "days"` when `column` already holds the number of days since the unit was last
active, rather than a 28-day bit pattern to decode. The no-rows value (30), the `< within_days`
comparison and the 28-day cap on `within_days` are all unchanged.

```toml
[metrics.active_in_last_3_days]
data_source = "firefox_desktop_active_users_view"
aggregation = "recency_within"
column = "days_since_desktop_active"
encoding = "days"
within_days = 3
```

## Ratios

`aggregation = "ratio"` divides one metric by another, such as a click-through rate. A ratio takes
no `data_source`, `column`, `where` or other aggregation field; it names its two components
instead:

```toml
[metrics.example_ratio]
friendly_name = "Example click-through rate"
numerator = "example_ratio_clicks"
denominator = "example_ratio_impressions"
aggregation = "ratio"
```

`numerator` and `denominator` each name a metric declared in `nimbus/` for the same application,
in either `definitions/`, `defaults/` or an outcome file. Neither may itself be a ratio. A ratio
may carry the usual metadata (`friendly_name`, `description`, `category`, `owner`, `deprecated`,
`level`, `statistics`), but not `cumulative_window`, `incremental_window` or `repeat_windows`: a
ratio takes its windows from its numerator and denominator, each resolved on its own.

A ratio generates no SQL of its own: `select_expression_from_aggregation` and
`bucketed_aggregation` are both `None` for a ratio metric. Its numerator and denominator are
ordinary metrics, each with its own `data_source` and aggregation, computed and reported
independently. See [Highwind](#highwind) for how `aggregation_plan()` exposes a ratio alongside
its components.

This mirrors how Jetstream already expresses a ratio in `definitions/` and outcomes: a metric with
`depends_on = [numerator, denominator]` and no SQL of its own, analysed with the
`population_ratio` statistic. See [Validation](#validation) for how a `nimbus/` ratio is checked
against that definition.

## Column forms

`column`, and a condition's `column`, may be a table instead of a plain column name, to read a
value out of a map or a JSON-valued column rather than a plain column:

| form | keys | SQL |
| --- | --- | --- |
| keyed-map, with a key | `map`, `key` | `mozfun.map.get_key(map, key)` |
| keyed-map, no key | `map` | `mozfun.map.extract_keyed_scalar_sum(map)` |
| JSON field | `json`, `path` | `JSON_VALUE(json, "$.path")` |

`map` and `json` take the same column name or dotted path as a plain `column`. A column form
declares exactly one of `map` or `json`; `key` is only valid with `map`, and `path` is required
with `json`. Highwind selects the underlying `map` or `json` column from the data source, the same
way it selects a plain `column`, including the projection a dotted path gets (see
[Highwind](#highwind)); the generated expression (`mozfun.map.get_key(...)` or `JSON_VALUE(...)`)
then reads that projected name.

```toml
[metrics.crlite_use_counter]
data_source = "metrics"
aggregation = "sum"
column = { map = "metrics.labeled_counter.cert_verifier_cert_revocation_mechanisms", key = "CRLite" }
```

```toml
[[metrics.pin_prompt_accepted.where]]
column = { json = "event_extra", path = "result" }
op = "="
value = "success_pinned"
```

A column form is a reference to one value, never an arbitrary expression; there is no function
call, cast or further nesting beyond the two forms above.

## Conditions

`where` is a list of conditions. A row matches when every condition holds; conditions in the list
are AND'd together. Each condition is either a clause or an `any_of` group of clauses, OR'd
together; see [OR within a condition](#or-within-a-condition).

Each clause is a table with these keys:

| key | required | meaning |
| --- | --- | --- |
| `column` | yes | A column name, a dotted path to one, or a column form. See [Column forms](#column-forms). |
| `op` | no | One of the operators below. Leave it out to test a boolean column for true. |
| `value` | with a comparison or list operator | The value, or list of values, to compare against. |

Operators:

| op | matches when | `value` |
| --- | --- | --- |
| `>` | column is greater than value | required |
| `>=` | column is greater than or equal to value | required |
| `<` | column is less than value | required |
| `<=` | column is less than or equal to value | required |
| `=` | column equals value | required |
| `!=` | column does not equal value | required |
| `LIKE` | column matches the pattern | required |
| `IN` | column equals one of a list of values | required, a non-empty list |
| `IS NULL` | column is null | not allowed |
| `IS NOT NULL` | column is not null | not allowed |
| (no `op`) | column is true | not allowed |

`value` is a number, string or boolean, except for `IN`, where it is a non-empty list of them. The
parser checks that `value` is present when the operator needs it, and absent otherwise. It does
not check the type of `value` or its elements. Generating SQL fails for a value, or list element,
of any other type.

Null handling: a comparison against a null column does not match. This includes `!=` and `IN`, so
`column != 0` and `column IN (0, 1)` do not match rows where the column is null. The boolean form
matches only true, not false or null. Use `IS NULL` or `IS NOT NULL` to test for null.

There is no NOT, function call or expression, beyond the column forms covered above.

```toml
[[metrics.release_days_with_search_engine.where]]
column = "normalized_channel"
op = "="
value = "release"

[[metrics.release_days_with_search_engine.where]]
column = "default_search_engine"
op = "IS NOT NULL"
```

### OR within a condition

A condition in `where` may instead be a table with one key, `any_of`, a list of at least two
clauses. The clauses OR together to form one condition, which AND's with the rest of `where` the
same as any other condition.

```toml
[[metrics.site_breakage_uses.where]]
any_of = [
  { column = "event_name", op = "=", value = "send" },
  { column = "event_name", op = "=", value = "send_more_info" },
]
```

OR nests no further: each clause inside `any_of` is a plain clause, never another `any_of`.

### The `column` shorthand

On `count_where` and `any`, `column = "x"` is the same as a single condition testing the boolean
column `x` for true. A metric gives either `column` or `where`, not both.

```toml
[metrics.is_default_browser]
data_source = "clients_daily"
aggregation = "any"
column = "is_default_browser"
```

is the same as:

```toml
[metrics.is_default_browser]
data_source = "clients_daily"
aggregation = "any"

[[metrics.is_default_browser.where]]
column = "is_default_browser"
```

## Threshold and scale

Both apply once, to the aggregated value for a window. They do not apply per row.

`threshold` compares the aggregated value with a number. The result is 1 when the comparison holds
and 0 otherwise, so a metric with a threshold is 0/1. `op` must be one of `>`, `>=`, `<`, `<=`,
`=`, `!=`, and `value` must be a number.

```toml
[metrics.retained]
data_source = "clients_daily"
aggregation = "sum"
column = "pings_aggregated_by_this_row"
threshold = { op = ">", value = 0 }
```

`scale` multiplies the final value by a number. When both are set, the threshold is applied first
and the scale second, so the result is 0 or the scale.

```toml
[metrics.default_browser_per_1000]
data_source = "clients_daily"
aggregation = "count_where"
column = "is_default_browser"
scale = 1000
```

## Keep nulls

`sum`, `sum_where` and `any` return 0 (or `FALSE`) for a unit with no rows, unless `keep_nulls` is
set. `keep_nulls = true` leaves that unit null instead. For `sum_where` and `any`, a unit that has
rows but none matching still gets 0 (or `FALSE`) either way; only a unit with no rows at all is
affected. Valid only for `sum`, `sum_where` and `any`: `count`, `count_where` and `recency_within`
are rejected, since none of them can return null for a unit with no rows.

Set `keep_nulls = true` when a unit with no rows had no opportunity to act, so it should drop out
of the mean rather than count as 0.

```toml
[metrics.example_sum_keep_nulls]
data_source = "clients_daily"
aggregation = "sum"
column = "example_column"
keep_nulls = true
```

## Windows

Three fields say which windows Highwind computes for the metric. Lengths are in days, counted from
each unit's enrollment. Day 0 is the enrollment day.

- `cumulative_window = N`: windows that start at day 0. Each covers everything from enrollment to the
  end of the window.
- `incremental_window = N`: back-to-back windows of N days, starting at day 0. Each covers only its
  own days, with nothing carried forward from earlier windows.
- `repeat_windows`: when `false`, each family set produces one window, the first N days. When
  `true`, the windows continue for as long as the experiment runs.

Leave a length out to skip that family. A metric with neither length is valid, and Highwind does not
compute it. `repeat_windows = true` requires at least one length.

Highwind produces a window only once it is complete, that is, once all of its days have data.

Windows each setting produces, for an experiment observed for 21 days:

| setting | windows (days, end exclusive) |
| --- | --- |
| `cumulative_window = 7`, `repeat_windows = true` | [0,7) [0,14) [0,21) |
| `incremental_window = 7`, `repeat_windows = true` | [0,7) [7,14) [14,21) |
| `cumulative_window = 3` | [0,3) |
| `incremental_window = 7` | [0,7) |
| `cumulative_window = 7`, `incremental_window = 7`, `repeat_windows = true` | cumulative [0,7) [0,14) [0,21), incremental [0,7) [7,14) [14,21) |

A metric has one length per family. Two one-off windows of different lengths, such as 3-day and
7-day retention, are two metrics.

0/1 metrics such as `retained` usually use incremental windows. Over a growing cumulative window
nearly every unit reaches 1.

Highwind builds all the windows in one analysis from one grid of equal-length buckets. The window
lengths used together in one analysis must fit a common grid. The schema does not check this. How
lengths that do not fit are handled is decided by Highwind.

Jetstream does not read the window fields. Its analysis windows are configured in
`jetstream/defaults/`.

## Winsorization

`winsorize_quantile` and `winsorize_threshold` are Highwind-only. Highwind clips a heavy-tailed
metric's value at a ceiling before computing statistics on it; these fields say where that ceiling
comes from. At most one may be set.

- `winsorize_quantile`: the cut point Highwind clips the upper tail at, `0 < q <= 1`. Leaving it
  unset means Highwind's own default, which is a different value than `1`: `winsorize_quantile = 1`
  turns winsorization off for this metric explicitly, while an unset field lets Highwind's default
  change later without touching the metric. This matches the vocabulary Jetstream and mozanalysis
  already use for the cut point (`CensorHighestValues.fraction`, `threshold_quantile`): a Jetstream
  `drop_highest = d` corresponds to `winsorize_quantile = 1 - d`, so Jetstream's
  `drop_highest = 0.0` is `winsorize_quantile = 1`.
- `winsorize_threshold`: a fixed upper bound, per 7 days, that Highwind clips at instead of a
  quantile.

Neither field is valid on a yes/no metric: `any`, `recency_within`, or any metric with a
`threshold`, since clipping a 0/1 value does nothing. Neither is valid on a `ratio` either; Highwind
clips the numerator and denominator independently, as ordinary metrics, before dividing them. See
[Ratios](#ratios).

Nothing reads these fields except Highwind. Jetstream does its own clipping through
`drop_highest` in its statistics configuration, unaffected by either field. Setting or leaving
unset either field never changes `select_expression_from_aggregation` or `bucketed_aggregation`;
the ceiling is applied by Highwind after computing the aggregation, not as part of it.

```toml
[metrics.urlbar_search_count]
data_source = "clients_daily"
aggregation = "sum"
column = "urlbar_search_count"
winsorize_quantile = 0.995
```

## Statistics

`statistics` is a table of tables. Each key is a statistic name and its table holds that
statistic's parameters. An empty table means no parameters.

```toml
[metrics.active_hours.statistics.linear_model_mean]

[metrics.active_hours.statistics.deciles]
```

Nothing reads this field in `nimbus/` yet. Jetstream takes statistics from
`definitions/` and `jetstream/defaults/`. The parser does not check statistic names.

## Data sources

A metric's `data_source` usually names a data source already defined in
`definitions/<application>.toml`. When a data source is used only by `nimbus/`
metrics, such as one that otherwise exists only inside an outcome file, it can be declared in any
of the application's own files instead, under a top-level `[data_sources]` table:

```toml
[data_sources.events_certerror]
from_expression = "(SELECT * FROM telemetry.events)"
submission_date_column = "submission_date"

[metrics.cert_error_page_loaded]
data_source = "events_certerror"
aggregation = "any"

[[metrics.cert_error_page_loaded.where]]
column = "event_name"
op = "="
value = "loaded"
```

A `[data_sources.<name>]` table here takes the same fields as a `definitions/` data source. Keys
are lowercased, matching `definitions/`.

A `data_source` reference on a metric resolves against `definitions/<application>.toml` first,
then across the application's own files under `nimbus/`, then against the data sources declared in
the application's Jetstream outcome configs. So a `nimbus/` metric can reference a data source that
exists only inside a Jetstream outcome, such as `jetstream/outcomes/<application>/<outcome>.toml`,
with no copy declared under `nimbus/`. `ConfigCollection.get_nimbus_data_source_definition(slug,
app_name)` and `aggregation_plan()` both resolve a data source this way. A data source declared the
same way in more than one of the application's outcome configs resolves to that shared definition;
one declared differently across outcome configs fails to resolve, naming the conflicting outcomes.
Resolving against a Jetstream outcome requires loading the `jetstream/` subtree alongside
metric-hub's root; a consumer that loads only the root cannot see the application's outcome configs
and so cannot resolve a data source declared only there.

A data source declared under `nimbus/` under a name that also exists in
`definitions/<application>.toml` must be identical to the `definitions/` copy. A name means one
data source per application, so a differing copy under the same name fails validation; an
identical copy is redundant but allowed. A data source name is also declared at most once across
an application's own files under `nimbus/`; declaring it in more than one file is a validation
error. See [Validation](#validation).

## Validation

metric-config-parser checks the following wherever it parses a metric definition, including
`definitions/`, `nimbus/`, experiment configs and outcomes:

- `select_expression` and `aggregation` are both set.
- Any other aggregation field is set without `aggregation`.
- `aggregation` is not one of the seven.
- A `ratio` has `data_source`, `column`, `where`, `within_days`, `threshold`, `scale`, `keep_nulls`,
  `encoding`, `cumulative_window`, `incremental_window` or `repeat_windows` set.
- A `ratio` has no `numerator` or no `denominator`, or they are equal.
- `numerator` or `denominator` is set on any aggregation other than `ratio`.
- `sum`, `count` or `recency_within` has no `column`, or has `where`.
- `count_where` or `any` has both `column` and `where`, or neither.
- `sum_where` does not have both `column` and `where` set.
- `recency_within` has no `within_days`, or `within_days` is not a positive integer.
- `within_days` is greater than 28.
- `within_days` is set on any other aggregation.
- `keep_nulls` is set on any aggregation other than `sum`, `sum_where` or `any`.
- `encoding` is set on any aggregation other than `recency_within`.
- A `column`, or a condition's `column`, is not a plain column name or dotted path, and is not a
  valid column form (see [Column forms](#column-forms)).
- A column form declares both `map` and `json`, or neither; declares `path` without `json`, or
  `key` with `json`; declares `json` without `path`; or has a key not listed in
  [Column forms](#column-forms).
- A clause, `any_of` group or threshold has a key not listed in this document.
- A clause has no `column`, or a threshold is missing `op` or `value`.
- A clause's `op` is not one of the listed operators.
- A comparison or `LIKE` operator has no `value`, `IN` has no non-empty list `value`, or `IS NULL`,
  `IS NOT NULL` or the boolean form has a `value`.
- `any_of` has fewer than two clauses.
- `threshold.op` is not one of `>`, `>=`, `<`, `<=`, `=`, `!=`, or `threshold.value` is not a
  number.
- `scale` is not a number.
- `cumulative_window` or `incremental_window` is set and is not a positive integer.
- `repeat_windows` is not a boolean, or is `true` with neither window length set.
- Both `winsorize_quantile` and `winsorize_threshold` are set.
- `winsorize_quantile` is not a number greater than 0 and at most 1.
- `winsorize_threshold` is not a positive number.
- `winsorize_quantile` or `winsorize_threshold` is set on a yes/no metric: `any`,
  `recency_within`, or any metric with a `threshold`.

Booleans are not accepted where a number or integer is required.

In `nimbus/`, a file is also rejected when:

- The file has a top-level key other than `metrics` or `data_sources`.
- A metric has `select_expression`.
- A metric has no `aggregation`, or has no `data_source` and is not a `ratio`.
- A metric has a key not listed in the field reference.

Across files. When several repositories or directories are loaded together, such as metric-hub,
`jetstream/` and `opmon/`, this check runs once on the merged set, so every `definitions/`
directory loaded counts:

- `data_source` does not name a data source in any loaded `definitions/<application>.toml`, nor in
  any of that application's own files under `nimbus/`, nor in any of that application's loaded
  Jetstream outcome configs, for the same application.
- A data source declared under `nimbus/` has the same name as one in
  `definitions/<application>.toml`, but the two differ.
- A data source declared under `nimbus/` has the same name as one declared in one of the
  application's Jetstream outcome configs, but the two differ.
- A `data_source` resolves only against the application's Jetstream outcome configs, and those
  configs declare it differently from one another.

Across an application's own files under `nimbus/`:

- A metric name is declared in more than one of `nimbus/definitions/<application>.toml`,
  `nimbus/defaults/<application>.toml`, and `nimbus/outcomes/<application>/<outcome>.toml`, in any
  combination.
- A data source name is declared in more than one of those same three locations, the same way.
- A `ratio`'s `numerator` or `denominator` does not name a metric declared across those three
  locations for the application, or names one that is itself a `ratio`. See
  [Ratios](#ratios).

metric-hub CI rejects a `nimbus/` file that fails any of these checks. A consumer that loads
metric-hub skips such a file with a warning instead, so metric-hub keeps loading for it, including
every other file under `definitions/` and `nimbus/`.

Between `definitions/` and `nimbus/`. metric-hub CI runs this check in `.script/validate.py`. It
does not run when a repository is loaded, so a mismatch fails CI without stopping consumers from
loading metric-hub:

- A metric defined under the same name in `definitions/<application>.toml` and under `nimbus/` for
  the application renders different SQL in each, or names a different `data_source`.
- A `ratio` defined under the same name in `nimbus/` and in `definitions/<application>.toml` or an
  outcome names a different pair of metrics than that metric's `depends_on`, or than its
  `population_ratio` statistic's `numerator`/`denominator` when one is set.

The `select_expression` generated for the `nimbus/` copy and the `select_expression` of the
`definitions/` copy are both rendered with the functions in `definitions/functions.toml`, so
`agg_sum` and `agg_any` are expanded. Runs of whitespace are collapsed, and whitespace just inside
parentheses is removed, before comparing. Metrics defined in only one of the two files are not
compared. `ConfigCollection.nimbus_definition_mismatches()` returns the metrics that differ,
reporting a `ratio` mismatch the same way as a SQL mismatch, with each side's numerator and
denominator in place of its `select_expression`.

metric-hub CI also dry-runs the SQL generated for every metric in a changed file under `nimbus/`, as
it does for `definitions/`. A `ratio` has no SQL, so it is not dry-run.

Not checked:

- Whether a column exists on the data source. The parser has no table schemas.
- Whether window lengths used together fit a common grid.
- Statistic names. The fields shared with `definitions/` get no checks beyond those `definitions/`
  applies.

## How consumers use an aggregation-form metric

metric-config-parser generates two shapes of SQL from the same fields, one for each consumer. In
the tables below, `c` is `column` and `p` is the conditions joined with AND (the `column` shorthand
is the condition `c`; an `any_of` condition is its clauses joined with OR, parenthesized when `where`
has more than one condition).

### Jetstream

Jetstream reads `definitions/` and uses `select_expression`. When a metric declares the aggregation
fields instead, metric-config-parser generates its `select_expression` while resolving the metric,
so Jetstream handles it like any other metric. `MetricDefinition.select_expression_from_aggregation`
returns the generated expression. `sum` and `any` call the `agg_sum` and `agg_any` functions from
`definitions/functions.toml`, so they render the same way as a hand-written expression. The window
fields are not used.

| aggregation | `select_expression` | rendered |
| --- | --- | --- |
| `sum` | `{{agg_sum("c")}}` | `COALESCE(SUM(c), 0)` |
| `sum_where` | `COALESCE(SUM(IF(p, c, 0)), 0)` | same |
| `count` | `COUNT(c)` | same |
| `count_where` | `COUNTIF(p)` | same |
| `any` | `{{agg_any("p")}}` | `COALESCE(LOGICAL_OR(p), FALSE)` |
| `recency_within` N | `COALESCE(MIN(mozfun.bits28.days_since_seen(c)), 30) < N` | same |
| with `threshold` | `<expression> <op> <value>` | |
| with `scale` k | `<expression> * k` | |
| with `keep_nulls = true` (`sum`, `sum_where`, `any` only) | drops the default above: bare `SUM(c)`, `SUM(IF(p, c, 0))` or `LOGICAL_OR(p)` | |

`any`, `recency_within` and a threshold produce a boolean. When a threshold or a scale follows a
boolean, the boolean is cast first, as `CAST(<expression> AS INT64)`, so the value is 0/1 as
described in Threshold and scale. For example, `sum` with a threshold of `> 0` and a scale of 10
renders as `CAST(COALESCE(SUM(c), 0) > 0 AS INT64) * 10`. See [Keep nulls](#keep-nulls) for the
`keep_nulls` field. With `recency_within`, `mozfun.bits28.days_since_seen(c)` above is `c` itself
when `encoding = "days"`; see [recency_within](#recency_within).

In both shapes, condition values become SQL literals. Numbers are written as they are and booleans
as `TRUE` or `FALSE`. Strings are single quoted, with `\`, `'` and `{` escaped. A number that is
not finite, or a value of any other type, fails.

When a metric is defined in both directories, CI checks that the `select_expression` generated
from `nimbus/` matches the one in `definitions/`, so moving a metric to `nimbus/` does not
change what Jetstream computes. See [Validation](#validation).

### Highwind

Highwind reads a metric from `nimbus/` when it is defined there. It scans each data
source once per analysis. It reduces each unit's rows once per bucket, then builds each window from
those bucket values. `MetricDefinition.bucketed_aggregation` returns a `BucketedAggregation`,
which splits the aggregation into four parts:

- `bucket_aggregate`: reduces a unit's rows in one bucket to a number.
- `combine`: how bucket values combine over a window.
- `no_rows`: the value for a unit with no rows in the window.
- `finalize`: applied once to the combined value. It carries the threshold and scale. It is a SQL
  template in which `{combined}` stands for the combined value, and `finalize_sql(x)` substitutes
  `x` for it.

| aggregation | `bucket_aggregate` | `combine` | `no_rows` | `finalize(x)` |
| --- | --- | --- | --- | --- |
| `sum` | `COALESCE(SUM(c), 0)` (`keep_nulls = true`: bare `SUM(c)`, `no_rows` `NULL`) | `SUM` | `0` | `x` |
| `sum_where` | `COALESCE(SUM(IF(p, c, 0)), 0)` (`keep_nulls = true`: bare `SUM(IF(p, c, 0))`, `no_rows` `NULL`) | `SUM` | `0` | `x` |
| `count` | `COUNT(c)` | `SUM` | `0` | `x` |
| `count_where` | `COUNTIF(p)` | `SUM` | `0` | `x` |
| `any` | `COUNTIF(p)` | `SUM` | `0` (`keep_nulls = true`: `NULL`) | `CAST(x > 0 AS INT64)` |
| `recency_within` N | `COALESCE(MIN(mozfun.bits28.days_since_seen(c)), 30)` | `MIN` | `30` | `CAST(x < N AS INT64)` |
| with `threshold` | unchanged | unchanged | unchanged | `CAST(finalize(x) <op> <value> AS INT64)` |
| with `scale` k | unchanged | unchanged | unchanged | `(finalize(x)) * k` |

`keep_nulls = true` does not change `finalize`, only `bucket_aggregate` (for `sum` and `sum_where`)
or `no_rows` (for `any`). For `sum`, a bare `SUM(c)` over a bucket with no rows, or where every
row's `c` is null, is `NULL` in SQL, and `SUM` combine ignores nulls, so `no_rows = "NULL"`
reproduces the same value Jetstream's bare expression would return for a unit with zero rows in the
whole window, and collapses correctly over a single bucket. For `sum_where`, `SUM(IF(p, c, 0))`
zeroes out a row that does not match `p`, so a bucket with rows but no matches is `0`, not `NULL`;
only a bucket with no rows at all is `NULL`, the same distinction `no_rows = "NULL"` carries for the
whole window. For `any`, `bucket_aggregate` (`COUNTIF(p)`) is unchanged either way, since a bucket
that has any rows at all always returns a real count, never null; only `no_rows` changes, so a unit
with zero rows in every bucket combines to `NULL` and `finalize` casts that to `NULL`, matching
Jetstream's bare `LOGICAL_OR(p)`.

With `recency_within`, `mozfun.bits28.days_since_seen(c)` above is `c` itself when
`encoding = "days"`, the same substitution as on the Jetstream side.

The columns Highwind reads from each data source are derived from the aggregation-form
definitions: every `column` and every condition column, grouped by `data_source`. A column form
(see [Column forms](#column-forms)) contributes its underlying `map` or `json` column, not the
generated expression. These are SELECT-list items for the source scan: a plain name stays as is,
and a dotted path is projected under a flat name with `__` in place of `.`
(`metrics.counter.x AS metrics__counter__x`). The bucketed aggregation reads that flat name instead
of the path, so `bucket_aggregate`, any condition built from the same column, and a column form's
generated expression all reference `metrics__counter__x`. Two columns that would project to the
same flat name is an error.

`aggregation_plan(configs, app_name, metric_names)` builds this grouping for a run. It looks up
each requested name with `get_nimbus_metric_definition`, and returns an `AggregationPlan`:

- `sources`: one `AggregationSource` per data source the resolved metrics read, keyed by data
  source name. Carries the resolved `from_expression`, `client_id_column`, `group_id_column`,
  `analysis_units`, `submission_date_column`, and the sorted union of columns every requesting
  metric needs.
- `metrics`: one `AggregationMetric` per resolved name, keyed by metric name. Carries the data
  source name, the `BucketedAggregation`, the window fields, `is_binary` (true for `any`,
  `recency_within`, or any metric with a `threshold`, the same rule used to validate
  [Winsorization](#winsorization), so the two cannot disagree), and `winsorize_quantile` and
  `winsorize_threshold`, passed through unchanged with `None` preserved. A `ratio`'s numerator and
  denominator are resolved into this dict like any other requested metric, even when only the
  ratio itself was requested; the ratio's own name is not a key here.
- `ratios`: one `AggregationRatio` per resolved `ratio`, keyed by metric name. Carries the
  `numerator` and `denominator` metric names, both of which are also keys in `metrics`.
- `missing`: requested names with no `nimbus/` definition for the app. A missing name never raises,
  so Highwind computes every name that resolved and reports the rest. A requested `ratio` whose
  numerator or denominator has no `nimbus/` definition (or is itself a `ratio`) goes here instead
  of in `ratios`.

Highwind's contract for a ratio is simple by design: `aggregation_plan()` only identifies the two
components and confirms both resolve. Highwind computes the numerator and denominator per unit per
window, the same as any other metric, and divides the two at the branch level, a delta-method
population ratio over the branch's units. That computation is Highwind's own, not part of this
package.

### Equivalence

The column and condition text is the same in both consumers. Only the wrapper differs. Over a
single bucket the four Highwind parts reduce to the Jetstream expression, so both consumers compute
the same value for a window. Highwind returns 0/1 integers where Jetstream returns booleans; that
is also why a threshold, `any` or `recency_within` collapses to the same *value* as the Jetstream
expression but not always the same SQL *text* (Highwind's `finalize` always casts to `INT64`,
Jetstream's `select_expression` only does when something follows a boolean base expression).

### Segments

A segment is not an aggregation-form metric. It keeps its existing SQL `select_expression` and
`data_source` in `definitions/<app>.toml`, the same definitions Jetstream and mozanalysis read, so
Highwind computes a segment from the same SQL rather than a ported definition.

`segment_plan(configs, app_name, segment_names)` resolves a list of shared segment names for an app
into what Highwind needs to compute them. It looks up each requested name with
`get_segment_definition` and returns a `SegmentPlan`:

- `sources`: one `SegmentSource` per segment data source the resolved segments read, keyed by data
  source name. Carries the resolved `from_expression`, `window_start`, `window_end`,
  `client_id_column`, `group_id_column` and `submission_date_column`.
- `segments`: one `SegmentMetric` per resolved name, keyed by segment name. Carries the data source
  name and the rendered `select_expression`.
- `missing`: requested names with no definition in `definitions/` for the app. A missing name never
  raises, so Highwind computes every name that resolved and reports the rest.

A segment's `select_expression` is written for mozanalysis's segment query
(`SegmentDataSource.build_query`), not as a standalone predicate. Some shared segments refer to that
query's aliases directly, such as `e.enrollment_date` or `ds.<column>`. A consumer running the SQL
itself must use the same shape:

- Enrollments aliased `e`, with `e.analysis_id` and `e.enrollment_date`.
- The data source's `from_expression` aliased `ds`, left joined on `ds.<client_id_column or
  group_id_column> = e.analysis_id`.
- `ds.<submission_date_column>` bounded both by literal dates (first enrollment date plus
  `window_start`, last enrollment date plus `window_end`) and by `e.enrollment_date` plus the same
  offsets. The literal bound lets BigQuery prune partitions, and some sources, such as
  `clients_last_seen`, require a partition filter.
- Grouped by `e.analysis_id`.

A segment data source whose `from_expression` references `{{experiment...}}` needs an experiment to
render. `segment_plan` resolves with no experiment in scope, so such a source raises rather than
silently resolving, the same as a templated `nimbus/definitions/` metric data source (see Highwind
above).

## Not supported yet

- Histograms and percentiles.
- Averages, or any aggregation that cannot be split into per-bucket values that combine into the
  window value.
- `count_distinct`.
- NOT, function calls and expressions in conditions or columns, beyond the dotted-path column
  names, column forms, and OR within a condition covered above. OR does not nest: an `any_of`
  group holds only plain clauses.
- A no-SQL segment format. Segments keep their existing SQL in `definitions/`; see Segments above
  for how Highwind resolves them.

## Example

A complete file for `nimbus/defaults/firefox_desktop.toml`:

```toml
[metrics.active_hours]
friendly_name = "Active hours"
description = "Time during which Firefox received user input."
data_source = "clients_daily"
aggregation = "sum"
column = "active_hours_sum"
cumulative_window = 7
repeat_windows = true

[metrics.active_hours.statistics.linear_model_mean]

[metrics.retained]
friendly_name = "Retained"
data_source = "clients_daily"
aggregation = "sum"
column = "pings_aggregated_by_this_row"
threshold = { op = ">", value = 0 }
incremental_window = 7
repeat_windows = true
```

[definitions/example_config.toml.example](definitions/example_config.toml.example) shows every
field.
