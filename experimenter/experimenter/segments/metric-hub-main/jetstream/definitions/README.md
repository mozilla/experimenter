# Definitions

This directory contains metric, data source and segment definitions that can be referenced from other configuration files without having to be redefined. Configuration files in this directory need to be named after the platform the definitions target.

Changes to these configurations require approval on a pull request.
Once merged, live experiments will get rerun so the new configurations can get applied. Experiments that have been completed in the past **will not be rerun automatically**, manual reruns need to be triggered if necessary.

Avoid making changes to existing metrics, as results might become inconsistent with experiment analysis results computed in the past.

The `functions.toml` configuration file contains definitions of functions a select expression can be passed into. These functions can be called as part of select expressions. For example:

```toml
[metrics.searches_with_ads]
data_source = "search_clients_engines_sources_daily"
select_expression = '{{agg_sum("search_with_ads")}}'
```