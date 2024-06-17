# Change Desktop Randomization ID from `normandy_id` to `group_id`

This document serves as a mirror of the [canonical decision document](https://docs.google.com/document/d/1NsZJ9FI7GwznulsD5vLUz60RiF2HJHShp57Lo_YV0RQ/edit). In the case of a descrepancy, the Google Doc should take precedence.

## Author

Daniel Berry

## Status

ACCEPTED: Option 1, switch to `group_id`. 

## Deciders

- **Data Science**: Daniel Berry (Jun 12, 2024)
- **Data Engineering**: Mike Williams (Jun 13, 2024)
- **Nimbus Engineering**: Jared Lockhart (Jun 12, 2024)

## Context and Problem Statement

As part of the Firefox Profile Management (FPM) project, Nimbus should adapt to a multi-profile environment. At a minimum, Nimbus must synchronize experiment state across profiles within a group. However, the introduction of a new group level id (`group_id`) presents the opportunity to resolve the existing profile vs installation discrepancy by migrating to `group_id` as the randomization unit.

### Motivation

As a general rule, “[the] randomization unit can not be more granular than the analysis unit” because “If [the] randomization unit is more granular, then for each analysis unit, the observation may contain various experiences from different treatments or the control.“ [ref](https://alexdeng.github.io/causal/abstats.html#randomization-unit-and-analysis-unit)

As an example, in a drug trial generally a single patient (randomization unit) would be given the drug or the placebo and the trial would be analyzed as the number of patients (analysis unit) who improved.

To use this analogy in the shared profiles/FPM multi-profile situation: it’s as if we give each person their own treatment (drug or placebo) but we measure to see the number of families that improve.

This is the primary mechanism behind how FPM will “break experimentation”: multiple profiles will enroll independently (on account of having multiple Nimbus IDs) yet their telemetry will be mixed together, rolled up to the “unit of measurement” or “unit of analysis”. This is problematic because:

- The telemetry unit contains data from both treatment variants or from a treatment variant and the default (non-experience) experience (we are unable to differentiate)
- The “potential outcome” for a telemetry unit depends on whether or not it created/used multiple profiles.

### Current Set of Randomization IDs

- **Firefox desktop**: Nimbus uses the normandy_id, a distinct ID that is generated internally upon creation/installation of a new profile and stored with the profile/installation.
- **Firefox Android/Firefox iOS**: Nimbus uses an internal nimbus_id, a distinct ID that is generated internally and stored on disk.
- **Cirrus (“Nimbus for Web”)**: each integrating application defines its own randomization_id. For example, Monitor uses its own user_id and Pocket (would have) used a session_id.

## Decision Drivers

### Required

1. Enrollments should be synchronized across profile groups
2. The same ID should be used for both (1) randomization and (2) analysis.
3. The ID should be exposed to telemetry (to satisfy 1.2)
4. Be available in early startup
5. Be independent of any experimental treatment.

### Desired

1. The ID should be random.
2. Build toward support for multiple simultaneous levels of randomization.

## Non-Goals

A migration plan to wind down existing experiments and transition new experiments to `group_id`.

## Considered Options

- Switch to `group_id`
- Stay the course.
- Switch to `client_id`.

## Decision Outcome

We recommend switching to the `group_id` as the unit of both randomization and analysis. This will align the assignment of experiment treatments to their telemetry & analysis. That is, under this option, our randomization unit and analysis unit would be the same. This is desired and satisfies principle 1 above.
This option will allow all profiles in a profile group to enroll into experiments and receive identical and deterministic branch allocations. That is, if one profile is assigned to treatment, all profiles in that group will be assigned to treatment. This mitigates the largest risk to valid causal inference (violation of the SUTVA principle for profile groups).
Currently shared or cloned profiles will continue to enroll into experiments, which is the same behavior as current day. However, existing work to mitigate the impact of these is in progress (see: Analysis of Failed A/A Tests).
This option paves the way for alternate integrations with alternative randomization IDs. For example, Suggest experiments may wish to randomize at the search session level. Providing a client-side Nimbus SDK implementation that uses an external (to Nimbus) randomization ID would build toward this capability.

### Goal satisfaction

#### Required:

1. Satisfied.
2. Satisfied.
3. Satisfied.
4. Satisfied.
5. Satisfied.

#### Desired:

1. Implementation-dependent
2. Satisfied

## Alternatives Considered

### Stay the Course

Under this option, Nimbus will continue to use the Nimbus ID. Nimbus will manually sync the Nimbus ID (and enrollment state) across profiles in a group. One enrollment will occur per profile-group (group of profiles under a single group ID). Experiments will use group ID as the aggregation unit for analysis (i.e., all data from profiles in the group will be aggregated into a single observation). Currently shared/cloned profiles would continue to enroll independently.

#### Requirement satisfaction

##### Required:

1. Satisfied.
2. Partial: IDs at the same level are used and so, in theory, should function as if the same ID is used.
3. Not satisfied.
4. Satisfied.
5. Satisfied.

##### Desired:

1. Satisfied
2. Not satisfied.

### Switch to `client_id`

Under this option, Nimbus would adopt an ID that is not synchronized across profile groups, which violates requirement 1.

#### Requirement satisfaction

##### Required:

1. Not satisfied.
2. Satisfied.
3. Satisfied.
4. Satisfied.
5. Satisfied.

##### Desired:

1. Satisfied
2. Not satisfied.
