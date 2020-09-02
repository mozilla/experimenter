# Build Nimbus Console As Part Of The Experimenter Code Base

* Status: decided
* Deciders: Kate Hudson
* Date: 2020-08-31

## Context and Problem Statement

Experimenter is a web application developed solely for the purpose of managing product experiments at Mozilla.  It was originally designed to manage the Shield experimentation workflow, and has expanded to include a comprehensive workflow for managing Normandy experiments.  Project Nimbus is being developed with very different core assumptions than the previous experimentation platforms, and it is unclear whether building on top of the existing Experimenter infrastructure or creating a new purpose specific application will best suit the project's needs.

## Decision Drivers <!-- optional -->

* Meeting Project Nimbus' needs in a rapid, continuous fashion with minimal downtime
  * the impact to (a) near-term goals of launching our first real set of feature experiments (b) mid-term goals of deprecating and replacing existing experimentation channels (Normandy pref-flips, leanplum) (c) long-term developer productivity and maintenance costs.
* Contributability by a large, distributed group of people with different backgrounds (web engineers, data engineers, data scientists)
* Fitting cohesively into the FXA engineering pipeline/culture
* Continuing to support the existing experimentation (Normandy) workflow until Normandy experiments can be deprecated and transitioned to Nimbus


## Considered Options

* Build On Top Of Experimenter
* Start A New Application In Python/Django
* Start A New Application in TypeScript/Node

## Decision Outcome

Chosen option: After careful consideration of both options, we have decided to adopt the proposal to build on top of Experimenter and invest in improvements. This includes work to create new models, improve and document a development workflow that can be used by all members of the team, and write a new front end in React. While we carefully considered the proposal to start a new application in Node/Typescript, we determined that the risk around the time to bring a new application up to parity and the operations overhead of maintaining parallel systems was too significant to adopt the proposal.

We already have a list of improvements we’d like to make – over the next few days we will work on clarifying any details, breaking things down, and getting everyone up to speed on running the existing code base.

## Pros and Cons of the Options

### Build On Top Of Experimenter

Much of the existing Experimenter infrastructure can be reused, which gives Project Nimbus a well established framework to build on top of.

- Pros
  - Single source of truth for all past/future experiments
    - Easily discover past results
    - Correlate past/future experiments easily
    - Generate high level reports for leadership/stakeholders across all experiment types
    - Consistent APIs for dependent automated tasks (ie data engineering/science)
  - Reuse existing components
    - Database schemas are largely reusable
    - Public APIs work seamlessly for Normandy and Nimbus experiments
    - External service integrations (bugzilla/remote settings/email/auth0) work seamlessly
  - Comprehensive development/testing/deployment infrastructure in place
    - 100% unit testing coverage across Python/JS/TS
    - Automated Selenium Integration tests for frontend
    - Continuous Deployment
  - Dynamic Risk Mitigation
    - There have been several cases where risk will need to set on different path for mitigation (partner involved, new metrics needed, new targeting needed). The goal is 100% to move to lighter weight/no review whenever possible - but kick the ones that need more hands-on into that flow.

- Cons
  - Existing workflow/UI not applicable
    - The existing workflow and UI is designed around a highly managed experimentation design process with multiple coordinators and sign-offs required, in which an additional set of tools is required for the actual launch and management of experiments. It is also, for the most part, based around the Firefox Desktop release management process.  Nimbus is intended to manage the whole process from experiment design to launch to monitoring, with a lighter-weight peer review process, in which individuals creating experiments are more responsible for the entire life cycle and viability of their own experiments.
  - Some database schemas require refactoring to isolate Normandy and Nimbus concerns
  - Careful consideration that adding Nimbus features does not disturb existing functionality
  - Lack of static typing (mypy can be added with effort)
  - Supporting both Normandy and Nimbus over time could cause unwanted complexity/duplication
  - [Current Experimenter codebase may not align with FXA tools/processes/practices](https://github.com/mozilla/fxa/blob/main/docs/adr/0020-application-architecture.md)
  - Somewhat constricted by core designs decisions that were made in service of existing Normandy experimentation workflows that may not apply to Nimbus

### Start A New Application In Python/Django

Creating a new web application in Python/Django would allow us to reuse much of the existing code/infrastructure where applicable while clearly isolating the concerns of supporting existing experiment types and building out new Nimbus functionality.

- Pros
  - Start by cloning the repo and deleting all the unnecessary UI/DB/APIs
  - Get a big head start by not needing to reimplement the reusable parts
  - Isolate Nimbus concerns without fear of breaking Normandy experiments
  - Consistent development and deployment workflow for both old and new applications
  - Opportunity to rethink core code/architectural/tooling decisions where appropriate
- Cons
  - Lose single source of truth
    - Possibly require people to know which application to refer to depending on experiment type
    - Possibly create an API proxy in front of both to have a single endpoint for dependent callers
    - More difficult to correlate experiments/learnings across the two applications
  - Changes that must apply to both Normandy and Nimbus experiments must be made in two places while they're both being actively maintained
  - Divergence in tooling/processes over time may create confusion when context switching between the two
  - Possibly still somewhat constricted by past core design decisions
  - [Python/Django may not align with FXA tools/processes](https://github.com/mozilla/fxa/blob/main/docs/adr/0020-application-architecture.md)
  - There is a cost to supporting teams, including cloud ops/IT/QA, to setting up and running an additional application

### Start A New Application in TypeScript/Node

Creating a new web application in TypeScript/Node would allow us to completely restart our thinking about the entire structure of the application which would result in both code and workflow/UI that are purpose built from the ground up to solely address the concerns of Nimbus experiments.

- Pros
  - Totally greenfield approach allows fresh perspectives to flourish
  - Stronger sense of collective ownership from all new contributors
  - Every decision and line of code built specifically to address the needs of Nimbus
  - TypeScript provides excellent feedback and guarantees which improves development experience
  - Native async/websocket support allows richer UI experience when coupled with SPA frameworks (like React)
  - [Fits more cohesively into the FXA team's tooling/processes](https://github.com/mozilla/fxa/blob/main/docs/adr/0020-application-architecture.md)
  - Logic/types in TS can be easily shared across multiple projects potentially including Desktop/Mobile clients
  - TS may integrate more smoothly with Rust than Python does to more tightly couple the server and the new Experiment Client
- Cons
  - Lose single source of truth
    - Possibly require people to know which application to refer to depending on experiment type
    - Possibly create an API proxy in front of both to have a single endpoint for dependent callers
    - More difficult to correlate experiments/learnings across the two applications
  - Changes that must apply to both Normandy and Nimbus experiments must be made in two places while they're both being actively maintained, but with the added complexity that one is in Python/Django and the other is in TS/Node which increases the context switching complexity
  - Node application frameworks are less mature than Django
  - No Django Admin Panel for easy data access
  - Forced to rewrite all the components that do still apply to both Normandy and Nimbus Experiments
    - Core db state/logic
    - Public and Private APIs
    - Dependent service integration (bugzilla/remote settings/email/auth0)
    - History/Changelog management
    - User roles/permissions
  - There is a cost to supporting teams, including cloud ops/IT/QA, to setting up and running an additional application

## Links <!-- optional -->

* [Decision Brief](https://docs.google.com/document/d/1AwtxZZAqP_2adyfDN5juTHW0TiuU8VV8VzDDo695kZQ/edit#)
* [New Experimenter Proposal](https://docs.google.com/document/d/1QMROYab-S5ZBL3oU_hoJxn5V2ocdPG5hlH_kYRMjO_4/edit?skip_itp2_check=true&pli=1)
