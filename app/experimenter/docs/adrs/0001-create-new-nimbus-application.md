# Create A New Web Application To Manage Nimbus Experiments

* Status: proposed
* Deciders: Kate Hudson, Jared Lockhart, TBD
* Date: 2020-08-18

## Context and Problem Statement

Experimenter is a web application developed solely for the purpose of managing product experiments at Mozilla.  It was originally designed to manage the Shield experimentation workflow, and has expanded to include a comprehensive workflow for managing Normandy experiments.  Project Nimbus is being developed with very different core assumptions than the previous experimentation platforms, and it is unclear whether building on top of the existing Experimenter infrastructure or creating a new purpose specific application will best suit the project's needs.

## Decision Drivers <!-- optional -->

* Meeting Project Nimbus' needs in a rapid, continuous fashion with minimal downtime
* Contributability by a large, distributed group of people with different backgrounds (web engineers, data engineers, data scientists)
* Fitting cohesively into the FXA engineering pipeline/culture
* Continuing to support the existing experimentation (Normandy) workflow

## Considered Options

* Build On Top Of Experimenter
* Start A New Application In Python/Django
* Start A New Application in TypeScript/Node

## Decision Outcome

Chosen option: TBD

### Positive Consequences

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* …

### Negative Consequences

* [e.g., compromising quality attribute, follow-up decisions required, …]
* …

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
- Cons
  - Existing workflow/UI not applicable
  - Some database schemas require refactoring to isolate Normandy and Nimbus concerns
  - Careful consideration that adding Nimbus features does not disturb existing functionality
  - Lack of static typing (mypy can be added with effort)
  - Supporting both Normandy and Nimbus over time could cause unwanted complexity/duplication
  - Current Experimenter codebase may not align with FXA tools/processes/practices
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

### Start A New Application in TypeScript/Node

Creating a new web application in TypeScript/Node would allow us to completely restart our thinking about the entire structure of the application which may result in both code and workflow/UI that are purpose built from the ground up to solely address the concerns of Nimbus experiments.

- Pros
  - Totally greenfield approach allows fresh perspectives to flourish
  - Stronger sense of collective ownership from all new contributors
  - Every decision and line of code built specifically to address the needs of Nimbus
  - TypeScript provides excellent feedback and guarantees which improves development experience
  - Native async/websocket support allows richer UI experience when coupled with SPA frameworks (like React)
  - Fits more cohesively into the FXA teams tooling/processes
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


## Links <!-- optional -->

* [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->
* … <!-- numbers of links can vary -->
