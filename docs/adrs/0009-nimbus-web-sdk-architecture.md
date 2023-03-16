# Nimbus Web SDK Architecture

* Status: proposed
* Deciders: James Hugman, Charlie Humphreys, Yashika Khurana, Jared Lockhart
* Date: 2023-15-03

Technical Story: https://mozilla-hub.atlassian.net/browse/EXP-3158

## Context and Problem Statement

This is part of a body of work necessary to support the use of Nimbus within web applications. 
The current Nimbus SDK is written in such a way that it supports client-oriented experimentation — experiments are downloaded, evaluated, and stored on the client, and a feature store is exposed with the experiment branches applied. 
In order to support web experimentation, the Nimbus SDK will need to be updated to be stateless, to support a more statically defined set of helper methods, and to have additional support for Python.

Ultimately, the problem we're trying to solve can be boiled down to one question — how can we update the Nimbus SDK to support web applications while continuing to support the existing clients?

## Decision Drivers

* Architecture decisions for Nimbus on the web[<sup>[1.i]</sup>](#links)
  * The core logic of the existing SDK will be re-used for the Nimbus web service (Cirrus)
  * The SDK needs to support Python
  * The SDK needs to be stateless

## Considered Options

* Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries
* Cargo features, one library
* Cargo features, separate library
* Expose a stateless API alongside the stateful API

## Decision Outcome

[justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

### Positive Consequences

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* …

### Negative Consequences

* [e.g., compromising quality attribute, follow-up decisions required, …]
* …

## Pros and Cons of the Options

### Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries

For this option, we would take the core Nimbus business logic currently in the `nimbus-sdk` library and move it to a new `nimbus-core` library. 
The `nimbus-sdk` and `cirrus-sdk` libraries would depend on the `nimbus-core` library, extending the functionality for their various use cases. 

* Good, because separate libraries allow for strong separation of concerns.
* Bad, because defining and using types becomes more difficult.
  * Traits will be needed to extend functionality in the Nimbus Core library. While dynamic typing with traits is supported, it is one of the more complex features of Rust.
* Bad, because it would result in a significant amount of code churn.

### Cargo features, one library

Cargo features allow for conditional compilation of libraries and library dependencies. 
Native Rust attributes are applied to sections of Rust code to conditionally compile structs, methods, variables, and more.

For more information, check out the Cargo Features reference[<sup>[1.ii]</sup>](#links) available in the Rust Cargo book.

* Good, because the use of feature configurations is familiar to Rust developers.
* Good, because all code relating to Nimbus business logic remains in one place.
* Good, because UniFFI bindings can be conditionally generated for each feature with different UDLs.
* Good, because dependencies can be excluded based on enabled features.
  * As an example, RKV will only be needed for Nimbus, so the RKV dependency will only be included in compilation when the `nimbus` feature is enabled.
* Good, because it will not increase the size of the existing Nimbus SDK binary.
* Bad, because onboarding developers learning Rust would likely have a more difficult time understanding Cargo features.

### Cargo features, separate library

This is roughly the same concept as above, but the features will be used in a different way.
Instead of features for both Nimbus and Cirrus, we would include a `stateless` feature in the Nimbus library to disable state-oriented features and dependencies.
The Cirrus library will then exist as a separate library from the Nimbus library.

* Good, because all the good things in the "Cargo features, one library" option above.
* Good, because the changes required will require minimal churn.
* Good, because better separation of concerns between Nimbus and Cirrus
* Bad, because defining and using types and traits across the libraries could prove difficult.
  * See a similar point in the "Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries" option above.
* Bad, because methods used across both libraries could result in collisions during development.

### Expose a stateless API alongside the stateful API

In this solution, we would expose static/stateless methods for interacting with experiments.
The UniFFI UDL would be updated to include the methods, resulting in the methods being visible in Android and iOS where they will not be used. 

* Good, because it's simple and entirely additive.
* Bad, because it makes Nimbus more prone to developer error.
* Bad, because it increases the size of the binary both for Cirrus and Nimbus.

## Links
1. Documentation
   1. [Nimbus on the Web Architecture Decision](https://docs.google.com/document/d/1ub46GXVz0rD6vsdS85UF_LvUfJItMwE9jicFCXc1jvw/edit?usp=sharing)
   2. [Cargo Features](https://doc.rust-lang.org/cargo/reference/features.html)