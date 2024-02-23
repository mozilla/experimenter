# Nimbus Metrics Guardrail Versioning

* Status: Decision proposed; accepting feedback
* Deciders: mwilliams@mozilla.com, dberry@mozilla.com, jlockhart@mozilla.com, ascholtz@mozilla.com
* Date: 2024-02-09
* Feedback by: 2024-02-20

## Context
- We want to change some Guardrail definitions
- Guardrails are hard-corded in Experimenter, so changing the identifier will mean they are not treated as Guardrails in Experimenter
- There is a task on the Roadmap to make guardrails configurable, but it is not currently prioritized high enough that we expect to do it this half
  - There is a possibility to make minimal changes in Experimenter to change the hard-coding of guardrails as a short-term solution
- Other tools may be affected by our decisions (e.g., OpMon, Looker)

## Proposed Decision: Option 2
All solutions have downsides, but this one fits best with the planned future task to make guardrails configurable, and also with the current practice of using `_v#` suffix to version metric definitions. It also minimally disrupts existing near-term plans and presents fewer (or no more) negatives or risks than other solutions.

## Decision Drivers
- Speed of implementation
  - this capability is wanted as soon as possible so that already-accepted guardrail metric changes can be made
- Fit with current/future plans
  - solution should fit with the planned future task to make guardrails configurable
  - solution should minimally disrupt current work (i.e., lower effort short-term is better)
- Complexity of maintenance
  - From perspective of both metric maintainers and developers of the system/tools
  - Things to consider: uses existing paradigms, affects (or not) other tools, ability to trace historical definitions, etc.

## Considered Options
1. Modify the existing metric in place
2. Add the new definition as a new metric
3. Rename existing metric and create new definition under current name

The following descriptions include the resulting state of the metric for the old and new definitions, assuming an initial single metric to-be-changed called `metric_name`.


### Option 1: Modify the existing metric in place
- Change the existing definition in metric-hub
- Old definition: no longer in metric-hub (only in git history)
- New definition: `metric_name`

#### Pros
- No changes needed to Experimenter
- Jetstream automatically manages metric versions based on timestamps and metric-hub commits, so each experiment can decide whether or not to adopt the new definition
#### Cons
- Harder for users to keep track of old definitions, which would still be used in older experiments
  - Would need to reference git history
- Non-Jetstream tools that use metric-hub (e.g., OpMon) do not have automatic version management for metric definitions, so they would adopt the new definition without option to decide
- No easy way to compare results of old and new definitions
- Probably not the best solution for other metrics or for when we have configurable guardrails


### Option 2: Add the new definition as a new metric
- Duplicate the current metric definition and rename the new one
- Modify the new metric with new definition
- Add new metric as guardrail in Experimenter
- Old definition: `metric_name`
- New definition: `metric_name_v2`

#### Pros
- Preserves history of definitions in an obvious lineage
- No chance of other tools erroneously adopting new definition
- Precedent for this with other metric definition changes
- Jetstream automatically manages metric versions based on timestamps and metric-hub commits, so each experiment can decide whether or not to adopt the new definition
#### Cons
- Requires Experimenter update in order for new metric to be shown as a guardrail
- Other tools may require updates to adopt new definition


### Option 3: Rename existing metric and create new definition under current name
- Duplicate the current metric definition and rename the old one
- Modify the new metric with new definition
- Old definition: `metric_name_old`
- New definition: `metric_name`

#### Pros
- No changes needed to Experimenter
- Jetstream automatically manages metric versions based on timestamps and metric-hub commits, so each experiment can decide whether or not to adopt the new definition
#### Cons
- Harder for users to keep track of old definitions, which would still be used in older experiments
  - Would need to know that the metric name changed
- Non-Jetstream tools that use metric-hub (e.g., OpMon) would adopt the new definition without option to decide
- Not very intuitive to change an existing metric name
