# Exposure events and coenrolling features

* Status: proposed
* Deciders: dberry@mozilla.com, jhugman@mozilla.com, jlockhart@mozilla.com, shell@mozilla.com
* Date: 2023-07-04, making the decision on or before 2023-07-11.

Technical Story: [Supporting exposure events for coenrolled features](https://mozilla-hub.atlassian.net/browse/EXP-3602)

## Context and Problem Statement

Application feature code can be configured from and by Nimbus. In the case of `messaging`, the complete set of messages and all their associated data is implemented by this feature configuration.

The feature configuration is composed by merging together the default configuration, any configuration from a rollout, and any configuration from experiments.

In the next release, features can be configured to enroll in more than one experiment on the same client device. Such features, known as coenrolling features, serve multiple treatments to the user (e.g. a `messaging` message) from different parts of the complete feature configuration.

It is not _currently_ possible to work from the part of the feature configuration backwards to the experiment to record an exposure event, giving credit for experiment that provided this treatment.

This ADR is deciding what to do— in the case of messaging— about the attribution of which experiment a particular message came from.

### Current status: no coenrollments

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

Chosen option: "Option 3: Add the experiment slug to the feature schema, so the experiment slug travels with the message", because it is the only option that meets the criteria set by the decision drivers.

### Positive Consequences

* Good, because implementation is relatively simple, and restricted to the client side.
* Good, because the correct number of exposure events are recorded.
* Good, because no extra steps needed in post experiment data-analysis.

### Negative Consequences

* Bad, because it involves a change to the feature JSON, and the user to change their behavior.

This has consequences for the implementation of `messaging` in Firefox for iOS and Firefox for Android, and some work in the Nimbus SDK, and documentation in experimenter.info.

## Pros and Cons of the Options

### Option 1: Record exposure events only when we're sure of which experiment is involved

In practice, this might be only for when exactly one experiment is using the `messaging` feature.

The message sending experiment owner should continue to use the `message-under-experiment` key.

Fewer exposure events will be emitted than should be.

* Good, because this requires little or no client side implementation
* Good, because this requires little or no data-analysis implementation.
* Good, because it involves no change to the feature JSON— the user interface for the message sender.
* Very Bad, because data-analysis result become much less useful, and needs to be aware what other experiments are active.

This is the current implementation.

### Option 2: Record the exposure event with the message key

The Glean event schema for exposure events would have an additional `part-id` extra, or even another type of exposure event created.

The message sending experiment owner should stop using the `message-under-experiment` key.

An exposure event is emitted for _every_ message that is displayed, even if the message came bundled with the app.

An extra manual step in data analysis is needed to get the message keys from the experiment, and then to match up the exposure events to the experiment.

* Bad, because it increases the number of false positive exposure events; increasing bandwidth and compute costs
* Bad, because it involves a change to the feature JSON, and the user to change their behavior.
* Bad, because it requires changes to the exposure event schema, which could affect every experiment.
* Bad, because it requires additional steps to the data-analysis, some of which will be impossible to automate.

### Option 3: Annotate the message with the experiment slug in the feature JSON

Instead of the user telling the feature which _message_ is under experiment, the user annotates the message with the _experiment_ slug.

i.e. remove the `message-under-experiment` property, and replace it with a new optional `experiment` message property.

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

When the experiment slug is known, e.g. at enrollment, the feature config is checked for strings containing `{experiment}`, and the slug used to replace it: i.e. the user should not need to type the actual slug.

When the message is displayed, the `experiment` property is the experiment slug; this can be used to look up the branch, and an exposure event then recorded.

* Good, because implementation is relatively simple, and restricted to the client side.
* Good, because the correct number of exposure events are recorded.
* Good, because no extra steps needed in post experiment data-analysis.
* Bad, because it involves a change to the feature JSON, and the user to change their behavior.

## Links

* [Experimenting with mobile messaging](https://experimenter.info/mobile-messaging/#experimenting-with-messages)
* [EXP-3602 Support for coenrollment features](https://mozilla-hub.atlassian.net/browse/EXP-3602) epic
