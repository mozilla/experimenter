# featmon — Nimbus Feature Monitoring Configs

This directory contains per-application TOML configuration files for Nimbus
feature monitoring (like `opmon/` is for operational monitoring).

Each file is named `<application>.toml` (e.g. `firefox_desktop.toml`) and
defines the BigQuery data sources and Nimbus features to monitor.  The BigQuery
**dataset** is inferred from the filename stem, so it does not need to be
repeated inside the file.

See [example_config.toml.example](example_config.toml.example) for a fully
annotated example.

## Structure

### `[data_sources.<name>]`

Each data source maps to a BigQuery table in the application's dataset.

| Key | Required | Description |
|-----|----------|-------------|
| `table_name` | yes | BigQuery table name within the application dataset |
| `type` | yes | One of `"metrics"`, `"event_stream"`, or `"clients_daily"` |
| `analysis_unit_id` | no | Field used to identify analysis units (default: `"client_info.client_id"`) |

#### `[data_sources.<name>.dimensions]`

Optional grouping dimensions.  Each key is a dimension name.  Use an inline
table `{ field = "..." }` to specify the BigQuery field if it differs from the
dimension name.  For constrained dimensions add `value_in` and `default_value`.

```toml
[data_sources.metrics.dimensions]
normalized_channel = {}
locale = { field = "client_info.locale" }
normalized_country_code = { value_in = ["CA", "DE", "FR", "GB", "US"], default_value = "OTHER" }
```

### `[features.<key>]`

Each feature key must be valid TOML (snake_case).  When the actual Nimbus
feature slug contains hyphens, add a `slug` field:

```toml
[features.address_autofill_feature]
slug = "address-autofill-feature"
```

#### `[features.<key>.metrics_by_source.<source>.<type>]`

Metrics to collect, grouped by data source and metric type.

Supported types: `boolean`, `quantity`, `labeled_counter`, `labeled_boolean`,
`string`, `event`.

For `event` metrics an extra level of nesting groups by category:

```toml
[features.my_feature.metrics_by_source.events_stream.event.my_category]
my_event = {}
```

Metric values are inline tables.  An empty table `{}` picks sensible defaults.
Common optional keys: `field`, `aggregators`, `label_in`.
