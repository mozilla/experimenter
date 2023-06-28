# Nimbus Web: Glean Application Structure

* Status: proposed
* Deciders: Daniel Berry, Eric Fixler, Yashika Khurana, Jared Lockhart, Alessio Placitelli, Jan-Erik Rediger, Anna Scholtz
* Date: 2023-06-13

Technical Story: https://mozilla-hub.atlassian.net/browse/EXP-3575

## Relevant Terminology

| Term                                                                                                           | Definition                                                                                                 |
|:---------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------|
| [Nimbus Web](https://docs.google.com/document/d/1ub46GXVz0rD6vsdS85UF_LvUfJItMwE9jicFCXc1jvw/edit?usp=sharing) | The project intended to bring the Nimbus experimentation platform to web-based applications.               |
| [Cirrus](https://github.com/mozilla/experimenter/tree/main/cirrus)                                             | The Docker container used to integrate Nimbus into web applications. It is deployed following the Sidecar  |

## Context and Problem Statement

Within the context of the Nimbus Web project, a single Cirrus container will need to support experimentation and data collection for multiple individual applications within the same product domain.
As an example, a single Cirrus container could be used to support experimentation for Pocket web, Pocket iOS, and Pocket Android.
All apps supported by a single Cirrus container, as best we can estimate at this time, will all be a part of the same product domain. 
In the previous example, the product domain is Pocket.

The problem this ADR addresses is as follows: with Cirrus, how should we structure Glean applications for cross-platform apps integrating Cirrus?

> #### Note
> Various explanations below will reference Pocket, but this ADR generally applies to all products planning to integrate Nimbus into their applications.  

## Decision Drivers

* Ease of data collation
  * How easy is it to collate data for an application?
  * How easy is it to collate data across applications?
* Glean Python SDK architecture

## Considered Options

* One Glean app ID
* One Glean app ID per domain
* One glean app ID per application

## Decision Outcome

Chosen option: "One Glean app ID per product domain", because it has the most advantages and fewest disadvantages _(see below)_. 
Option "One Glean app ID" is also viable, but it could come with additional disadvantages in the form of conflicting data retention policies across product domains.
Option "One glean app ID per application"'s disadvantages are simply too detrimental to the project for the option to be viable.

### Positive Consequences

* Its usage will work with the existing Glean Python SDK architecture
* Collating data for one app and across apps is straightforward
* Probe-scraper repository list will have overall fewer listings for Nimbus web applications than the current model
* Sidecar deployment model remains viable within Pocket's architecture
* Data retention can be set differently for each product domain

### Negative Consequences

* Jetstream will require changes in order to support this choice
* We are breaking away from our historical standard of Glean practices
* We may have to make more intensive changes to Experimenter

## Pros and Cons of the Options

### One Glean app ID

With this option, we would have one Glean application ID that is shared across all instances of Cirrus.
All applications using Cirrus would share a single Glean application ID, allowing for an overall lower maintenance burden for probe-scraper and easier collation of data across applications.
One downside of this solution is that data from multiple product domains will exist within the same table structure.

* Good, because it has the smallest footprint in the probe-scraper repository of the listed options.
* Good, because the Glean SDK supports this particular use case.
* Good, because this model supports Pocket's architecture.
* Bad, because data retention cannot be handled separately for each application or product domain.
* Bad, because it breaks away from our existing Glean usage practices.
* Bad, because it requires changes to Jetstream.
  * At this time, the nature and timeline of these changes is unclear.
* Bad, because it could require more changes to Experimenter than we already expect.
  * While we will still need to add new applications, it is also possible we will need to adjust how applications are handled in Experimenter.

### One Glean app ID per product domain

In this option, we would have one Glean application ID that is shared across all applications within a given product domain.
As an example, this might look like all Pocket applications (web, iOS, Android) sharing a single `cirrus_pocket` Glean app ID, but MDN, VPN, Relay, and others would have app IDs for their own product domains.
In order to support this, additional information would be sent alongside Glean metrics, such as a source application ID and app channel.
This gives us the benefits of having fewer total Glean app IDs, while also granting additional benefits such as separate retention periods for each product domain.

* Good, because it has a smaller footprint in the probe-scraper repository.
* Good, because applications within a single product domain will share a single table structure.
* Good, because the Glean SDK supports this particular use case.
  * The Glean application would be set separately from the Nimbus application context.
* Good, because this model supports Pocket's architecture.
* Good, because data retention can be set by each product domain planning to use Cirrus.
* Bad, because it breaks away from our existing Glean usage practices.
* Bad, because it requires changes to Jetstream.
  * At this time, the nature and timeline of these changes is unclear.
* Bad, because it could require more changes to Experimenter than we already expect.
  * While we will still need to add new applications, it is also possible we will need to adjust how applications are handled in Experimenter.

### One glean app ID per application

This is the existing pattern — one Glean application ID for each individual application we will support.
In this option, Pocket's various applications would each have their own listing in probe-scraper.
This option likely requires the fewest changes to Jetstream and Experimenter, instead moving the complexity to the Cirrus pod, deployment architecture, or Pocket's code.

* Good, because it follows our existing Glean usage practices.
* Good, because it requires few to no changes to Jetstream.
* Good, because it only requires the expected number of changes to Experimenter (adding new applications).
* Bad, because its long-term impact on us by adding a significant number of new applications is unclear.
* Bad, because each application has overhead in the form of development maintenance in the probe-scraper repo.
* Bad, because each application has its own table structure within our ingestion architecture, making joining data across applications a taxing process.
* Bad, because the Glean SDK is written to function as a singleton.
  * Within the Glean Python SDK, Glean is a singleton. We cannot create more instances of Glean without having separate Python processes.
  * We could use the Glean Rust SDK to instantiate multiple instances of the Glean client at once, but that has only been done for testing purposes.
* Bad, because Pocket's backend inherently supports all their applications — web, iOS, and Android.
  * A deployment-based solution here would be for Pocket to deploy one Cirrus container for each application, and make sure to send the enrollment request to the correct container.
    As there are potentially multiple places the Cirrus container will need to be deployed as-is, the number of Cirrus containers needed to support this deployment model is significantly higher than a single-container deployment model. 

## Links

* [Glean Python SDK docs](https://mozilla.github.io/glean/book/user/adding-glean-to-your-project/python.html)
* [Probe-scraper repository list](https://github.com/mozilla/probe-scraper/blob/main/repositories.yaml)
* [Nimbus on the Web Architecture Decision](https://docs.google.com/document/d/1ub46GXVz0rD6vsdS85UF_LvUfJItMwE9jicFCXc1jvw/edit?usp=sharing)
* [Cirrus code](https://github.com/mozilla/experimenter/tree/main/cirrus)
