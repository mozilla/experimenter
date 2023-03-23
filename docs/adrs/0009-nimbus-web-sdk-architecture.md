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

As an example of what the Cirrus API might look like, we can likely expect endpoints to perform the following:
* Enroll a user into available experiment(s)
  * This would return the enrolled experiments as well as the feature values given the enrollments
* Fetch the default feature values
* Fetch the feature manifest
* Fetch a specific feature value given enrolled experiments

## Decision Drivers

* Architecture decisions for Nimbus on the web[<sup>[1.i]</sup>](#links)
  * The core logic of the existing SDK (Rust) will be re-used for the Nimbus web service (Cirrus)
  * The SDK needs to support Python via UniFFI
  * The SDK needs to be stateless

## Considered Options

* Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries
* Cargo features, one library
* Cargo features, separate library
* Expose a stateless API alongside the stateful API (Do nothing)

## Decision Outcome

We have decided to move forward with option number 2, "Cargo features, one library".
This option, like the others mentioned, meets the key decision drivers.
We believe using this option will be the most maintainable long-term, despite the added complexity of using cargo features.
In addition, implementing this option has a similarly short timeline and amount of work necessary as compared to the "Cargo features, separate library" option, without the additional overhead of more complex typing.

### Positive Consequences

* Meets all decision drivers.
* Small amount of work necessary with a very limited amount of code churn.

### Negative Consequences

* It will be difficult to draw boundaries between Cirrus and Nimbus code.
* We could run into unexpected issues with UniFFI, as multiple UDL files in a single crate has not yet been tested. 

## Pros and Cons of the Options

### Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries

For this option, we would take the core Nimbus business logic currently in the `nimbus-sdk` library and move it to a new `nimbus-core` library. 
The `nimbus-sdk` and `cirrus-sdk` libraries would depend on the `nimbus-core` library, extending the functionality for their various use cases. 

#### Pros
* Separate libraries allow for strong separation of concerns.
  * Changes in the `cirrus-sdk` library will not require changes the `nimbus-sdk` library.
  * Certain Nimbus-only features (such as the event store) will not available in the Cirrus library. 
* Dependencies can be excluded based on enabled features.
  * As an example, RKV will only be needed for Nimbus, so the RKV dependency will only be included in compilation when the `nimbus` feature is enabled.
* It will not increase the size of the existing Nimbus SDK binary.
* All code relating to core Nimbus business logic remains in one place.

#### Cons
* Defining and using types becomes more difficult.
  * Traits will be needed to extend functionality in the Nimbus Core library[<sup>[2.i]</sup>](#links).
    While dynamic typing with traits is supported, it is quite complex.
* Would result in a significant amount of code churn.
  * Many methods, structs, and other sections of code would need to move to the new `nimbus-core` library. 
    Additionally, a number of methods would need to have their call signatures updated.

### Cargo features, one library

Cargo features allow for conditional compilation of libraries and library dependencies. 
Native Rust attributes are applied to sections of Rust code to conditionally compile structs, methods, variables, and more.

For more information, check out the Cargo Features reference[<sup>[1.ii]</sup>](#links) available in the Rust Cargo book.

#### Pros
* The use of feature configurations is familiar to Rust developers.
* All code relating to Nimbus business logic remains in one place.
* UniFFI bindings can be conditionally generated for each feature with different UDLs.
* Dependencies can be excluded based on enabled features.
* It will not increase the size of the existing Nimbus SDK binary.

#### Cons
* Onboarding developers learning Rust would likely have a more difficult time understanding Cargo features.
* Cirrus and Nimbus logic within the same crate could make it harder to draw boundaries between the logic for each feature.
* This will be the first time we have included more than one UniFFI UDL in a single crate, and could run into unexpected issues.

### Cargo features, separate library

This is roughly the same concept as above, but the features will be used in a different way.
Instead of features for both Nimbus and Cirrus, we would include a `stateless` feature in the Nimbus library to disable state-oriented features and dependencies.
The Cirrus library will then exist as a separate library from the Nimbus library, primarily to function as a more visible separation of concerns between the two libraries.
The new Cirrus library would mostly consist of the Cirrus UDL, as well as helper methods — e.g: parsing JSON received from Python before getting to the core function or other things along those lines.

#### Pros
* All the good things in the "Cargo features, one library" option above.
* The changes required will require minimal churn.
* Better separation of concerns between Nimbus and Cirrus.
* Defining and using types and traits across the libraries could prove difficult.
  * See a similar point in the "Separate `nimbus-core`, `nimbus-sdk`, and `cirrus-sdk` libraries" option above.
* Dependencies can be excluded based on enabled features.
* It will not increase the size of the existing Nimbus SDK binary.

#### Cons
* Onboarding developers learning Rust would likely have a more difficult time understanding Cargo features.
* Cirrus calling methods within Nimbus could make it harder to draw boundaries between the logic for each feature.
  * Changes to method signatures in Nimbus could result in unexpected/unnecessary changes being required for Cirrus.

### Expose a stateless API alongside the stateful API (Do nothing)

In this solution, we would expose static/stateless methods for interacting with experiments.
The UniFFI UDL would be updated to include the methods, resulting in the methods being visible in Android and iOS where they will not be used. 

#### Pros
* It's simple and _mostly_ additive.

#### Cons
* It makes Nimbus more prone to developer error.
  * This is a "someone finds the function in the Nimbus internals and starts using it incorrectly" concern.
  * As an example, the existing Nimbus SDK UDL includes a NimbusClient that compiles into direct FFI bindings into the Rust code. It does not include any utilities for threading methods that require persistence or object builders. This class shouldn't ever actually be used by iOS/Android directly, but it is there and _can_ be used. 
  * By adding the stateless methods for experiment evaluation (and others), they would be available in Python, Kotlin, and Swift, even though they should only be used within the context of Cirrus.
* It increases the size of the binary both for Cirrus and Nimbus.

## Links
1. Documentation
   1. [Nimbus on the Web Architecture Decision](https://docs.google.com/document/d/1ub46GXVz0rD6vsdS85UF_LvUfJItMwE9jicFCXc1jvw/edit?usp=sharing)
   2. [Cargo Features](https://doc.rust-lang.org/cargo/reference/features.html)
2. Examples
   1. [Multi-module typing example](https://github.com/jeddai/application-services/pull/1/files#diff-02305e8e02a7900352e67be1fd2eef0b5a7c7cf91f4cc3e4559668c124d34e88R11-R19)  
