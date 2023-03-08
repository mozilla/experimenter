# Monitoring Data Import

* Status: proposed
* Deciders: Sunah Suh, Anna Scholtz, Jared Kerim
* Date: 2020-11-12


## Context and Problem Statement

Currently, Jetstream is responsible for daily processing experiment data for analysis after enrollment has completed. We're also interested in processing experiment data for monitoring purposes. Monitoring data is a little different from analysis data in that it is live (updated every few minutes) and needs to be available immediately when an experiment starts collecting data. Also, unlike analysis data, monitoring data sacrifices absolute accuracy for timeliness in order to detect big problems early. Jetstream is only responsible for generating analysis data and we need an alternative approach to access monitoring data from Experimenter.

Currently, [Grafana](https://grafana.telemetry.mozilla.org) is used to display monitoring data. It works by querying live tables from BigQuery on-demand and does not have any caching. We would like to eventually replace Grafana capabilities with custom visualizations inside of Experimenter. The goal is to have more flexibility than Grafana gives for how to display the data as well as less overhead for users when context switching from one visualization platform to another.

## Decision Drivers

* Data needs to be displayed "live", updating within minutes
* Cost needs to stay low
* Have flexibility with how the data is visualized
* Data loading speed


## Considered Options

1. Periodic ETL Output in GCS bucket
2. Query Data On-Demand from Experimenter
3. Embed Existing Grafana Graphs
4. Option (1) + ETL Optimizations


## Decision Outcome

##### Chosen option: "(2) Query Data On-Demand from Experimenter short term and (4) Optimize the ETL long term"

Option (3) has too many cons compared to (1), (2) and (4) so it can be dismissed.
Option (1) is fast but will be quite expensive compared to Option (2) and (4) so it can also be dismissed.
Option (2) would be slower than (1) and (4) but it is cheaper than (1) and (3). Although Option (2) is slow, it would not be any slower than Grafana currently is for loading data. In some cases when the cache is hit, it would be faster than Grafana.
Option (4) has the potential to be the cheapest but it cannot be implemented immediately as it needs some further breakdown.

It would be ideal to implement option (2) immediately to get some basic user-friendly monitoring in experimenter as soon as possible while continuing work on option (4). Once (4) ETL optimizations are complete, the Experimenter backend can switch to pulling data from this new source.

For this first pass at adding monitoring data, only basic user counts per branch and experiment health metrics will be added.


## Pros and Cons of the Options

#### (1) Periodic ETL Output in GCS bucket

Add ETL in [biguqery_etl](https://github.com/mozilla/bigquery-etl) to process the live data periodically and output results to a gcs bucket that can be accessed by Experimenter. This is how Jetstream data is currently being accessed. This would be the same ETL that runs on-demand from Grafana now, but instead would run once every 5-10 minutes.

* Pros:
  * No additional complexity for data processing in Experimenter
  * Allows flexibility for how data is visualized in Experimenter
  * Data will load faster coming from a bucket than needing to wait for a BigQuery query to run
* Cons
  * Since, so far, the demand on Grafana is low, this option to run the full ETL queries every 10 minutes or so may be much more expensive than option (2) or (3) 

#### (2) Query Data On-Demand from Experimenter
Add a background celery task that fetches data on-demand from bigquery and stores it in Redis. Redis cache can be used for the next fetch of the same data, but it gets invalidated periodically.

* Pros:
  * It won't be any slower than the current Grafana graphs
  * Allows flexibility for how data is visualized in Experimenter
  * The caching layer would make this approach the same price or cheaper than (1) and (3)
* Cons
  * This may be a little slow from the user's perspective compared to having the data computed in the ETL in advance (1)
  * Requires building complex data fetching, processing and storage logic directly in Experimenter, which means more tests and maintenance burden
  
#### (3) Embed Existing Grafana Graphs
Embed existing Grafana graphs (e.g. [graphs](https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=bug-1656561-rapid-testing-demo-nightly-80&from=1596153600000&to=1598832000000))

* Pros:
  * The simplest and quickest solution
* Cons
  * Does not allow for flexibility in how data is visualized in Experimenter
  * Slow compared to (1)
  * Could be more expensive than (2) unless a caching layer is added


#### (4) Option (1) + ETL Optimizations
Option (1) would be the ideal solution if it was not the most expensive. This ADR initiated ideas about ETL optimizations for option (1) to be implemented with much lower costs.

The idea is to add an hourly job that looks almost exactly like the [daily job](https://github.com/mozilla/bigquery-etl/blob/master/sql/moz-fx-data-shared-prod/telemetry_derived/experiment_enrollment_aggregates_v1/query.sql) that already runs to aggregate 5-minute intervals of live data. Instead, however, the filter would be for 1 hour instead of 1 day and it would operate on the live table instead of `telemetry_derived.event_events_v1` (which is only updated daily). It would append to a table once per hour with the 5-min interval aggregations. This new table would be included as a third table in the [union for `all_enrollments`](https://github.com/mozilla/bigquery-etl/blob/master/sql/moz-fx-data-shared-prod/telemetry_derived/experiment_enrollment_aggregates_live/view.sql.py#L80) in [this view](https://github.com/mozilla/bigquery-etl/blob/master/sql/moz-fx-data-shared-prod/telemetry_derived/experiment_enrollment_aggregates_live/view.sql.p).

Finally, a python script would need to be created as an alternative to the existing on-demand Grafana queries. This script would generate a query that processes the data for every graph and for every experiment. It would also be responsible for handling aggregation granularity depending on the duration of the experiment so far. For example, experiments that have been running for < 1 hour might only have 5-min aggregations while those running for 1+ days would record daily aggregations.

* Pros:
  * No additional complexity for data processing in Experimenter
  * Allows flexibility for how data is visualized in Experimenter
  * Data will load faster coming from a bucket than needing to wait for a BigQuery query to run
  * Given the cost analysis completed so far, this has potential to be cheaper than (1), (2), and (3)
* Cons
  * This approach still needs a more detailed proposal and break-down and some confirmation of what the costs are
