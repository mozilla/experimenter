# Exposure events and coenrolling features

* Status: proposed
* Deciders: dberry@mozilla.com, jhugman@mozilla.com, jlockhart@mozilla.com, shell@mozilla.com
* Date: 2023-07-04, making the decision on or before 2023-07-11.

Technical Story: [Supporting exposure events for coenrolled features](https://mozilla-hub.atlassian.net/browse/EXP-3602)

## Context and Problem Statement

The feature configuration is composed by merging together the default configuration, any configuration from a rollout, and any configuration from experiments.

Features can now be configured to enroll in more than one experiment on the same client device. Such features, known as coenrolling features, serve multiple treatments to the user (e.g. a `mmessaging` message, or an `onboarding` card) from different parts of the complete feature configuration.

It is not currently possible to work from the part of the feature configuration backkwards to the experiment to record an exposure event, giving credit for experiment that provided this treatment.

Currently, for [experimenting with mobile `messaging`](https://experimenter.info/mobile-messaging/#experimenting-with-messages), the message sender (the user) must identify which message or messages are under experiment, then the system works out the experiment. For example, the feature JSON for annotating a message as being under experiment is:

```json
{
    "messages": {
        "my-first-message": { … }
    },
    "message-under-experiment": "my-first-message"
}
```

This works because:

1. the key `message-under-experiment` comes from exactly zero or one experiments
2. if the message being displayed is named as being under experiment, then the feature is in an experiment, and the system can deduce _which_ experiment.

The [`is-control` message property](https://experimenter.info/mobile-messaging/#control-messages) is used to label messages that are control messages.

```json
{
    "messages": {
        "my-first-message": {
            "trigger": [ … ],
            "surface": "notification",
            "is-control": true,
        }
    }
}
```

## Decision Drivers

* Data quality: the quality of the experimentation platform rests upon the quality and completeness of the data it has to analyse.
* Speed of implementation: we wish to implement this by the next release.
* Scalability: this should scale for features other than `messaging`, and for many experiments per feature.

## Considered Options

1. Record exposure events only when we’re sure of which experiment
2. Record exposure events, not with the experiment slug, but a part id, e.g. the message key.
3. Add the experiment slug to the feature schema, so the experiment slug travels with the message.

## Decision Outcome

Under consideration. Please submit comments before 2023-07-11.

<!-- Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)]. -->

<!-- ### Positive Consequences

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* …

### Negative Consequences

* [e.g., compromising quality attribute, follow-up decisions required, …]
* … -->

## Pros and Cons of the Options

### Record exposure events only when we're sure of which experiment is involved

In practice, this is might be for when exactly one experiment is using the `messaging` feature.

The message sending experiment owner should continue to use the `message-under-experiment` key.

Fewer exposure events will be emitted than should be.

* Good, because this requires little or no client side implementation
* Good, because this requires little or no data-analysis implementation.
* Good, because it involves no change to the feature JSON— the user interface for the message sender.
* Very Bad, because data-analysis result become much less useful, and needs to be aware what other experiments are active.

This is the current implementation.

### Record the exposure event with the message key as well as the experiment slug

The Glean event schema for exposure events would have an additional `part-id` extra, or even another type of exposure event created.

The message sending experiment owner should stop using the `message-under-experiment` key.

An exposure event is emitted for _every_ message that is displayed, even if the message came bundled with the app.

An extra manual step in data analysis is get the message keys from the experiment, and then to match up the exposure events to the experiment.

* Bad, because it increases the number of false positive exposure events; increasing bandwidth and compute costs
* Bad, because it involves a change to the feature JSON, and the user to change their behavior.
* Bad, because it requires changes to the exposure event schema, which could affect every experiment.
* Bad, because it requires additional steps to the data-analysis, some of which will be impossible to automate.

### Annotate the message with the experiment slug

Instead of the user telling the feature which messaage is under experiment, the user annotate the message with the experiment slug.

```json
{
    "messages": {
        "my-first-message": {
            "experiment": "{experiment}"
            …
        }
    }
}
```

When the experiment slug is known, e.g. at enrollment, the feature config is checked for strings containing `{experiment}`, and the slug used to replace it.

When the messgae is displayed, the `experiment` property is the experiment slug; this can be used to look up the branch, and an exposure event then recorded.

* Good, because implementation is relatively simple, and restricted to the client side.
* Good, because the correct number of exposure events are recorded.
* Good, because no extra steps needed in post experiment data-analysis.
* Bad, because it involves a change to the feature JSON, and the user to change their behavior.

## Links

* [Experimenting with mobile messaging](https://experimenter.info/mobile-messaging/#experimenting-with-messages)
* [EXP-3602 Support for coenrollment features](https://mozilla-hub.atlassian.net/browse/EXP-3602) epic
