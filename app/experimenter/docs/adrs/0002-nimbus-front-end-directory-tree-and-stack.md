# Nimbus Front-End: Directory Tree Changes and Use React/CRA, Bootstrap, and GQL

- Status: accepted
- Deciders: Lauren Zugai, Jody Heavener, Kate Hudson, Jared Lockhart
- Date: 2020-09-09

## Context and Problem Statement

The front-end for Experimenter is currently composed of two applications. The application currently being used in production for legacy experimentation, survey, and delivery channels including Normandy pref-flips, roll-outs, and heartbeat surveys, lives at `app/experimenter/static/core`. It is composed of a mix of Django templates, vanilla JS, jQuery, and React components, and uses a combination of Bootstrap CSS, `react-bootstrap`, and custom CSS. A newer React application for Nimbus experiments (previously named Rapid experiments) can be found at `app/experimenter/static/rapid` and uses only Bootstrap CSS.

With the decision made to build the Nimbus console as part of the Experimenter codebase ([see ADR #0001](https://github.com/mozilla/experimenter/blob/main/app/experimenter/docs/adrs/0001-build-nimbus-console-in-experimenter.md)), it was determined we likely want a "new front-end." After that ADR was merged, through discussions it was agreed upon that [graphene-django](https://github.com/graphql-python/graphene-django) would be used in the back-end, allowing the use of GQL in the Nimbus UI.

This ADR, while slightly atypical as it does not serve to document a single architectural change, outlines a proposed directory tree change regarding the front-end, a proposed new front-end stack, how it compares to the current `rapid` stack, and how we will benefit from these changes.

## Decision Drivers

Drivers for directory tree changes:

- A more obvious separation of concerns for:
  - the front-end and back-end
  - legacy front-end code and Nimbus front-end code

Drivers for the proposed new stack:

- Development speed
- Better development tooling which is especially important since we intend to move a lot of application logic to the front-end
- A more cohesive fit into the FxA team's stack and processes

Drivers for starting a new application:

- Time needed and ease of refactoring the current `rapid` React application vs time needed to start with a new application

## Proposed Changes

### App Directory Tree

Currently, a `static/` directory contains the front-end applications with some shared assets, and a `templates/` directory lives adjacent to it. To provide a more obvious separation of concerns in the directory tree:

- Rename `static/` to `legacy-ui/` since `static/rapid/` will become obsolete and `static/core/` will be the legacy Normandy platform¹
- Move `templates/` into `legacy-ui/` and add a README with historical information
- Use `create-react-app` to create a new React application in `app/experimenter/nimbus-ui/` with a README for development documentation

¹2020-09-15 clarification: `legacy-ui` will contain the `core` and `rapid` projects. When `nimbus-ui` reaches parity with `rapid`, we can delete the `rapid` directory. Once Nimbus can replace all experimentation moving forward and we either make legacy experiment data available in Nimbus or archive it elsewhere, we can then delete the entire `legacy-ui` directory.

### Front-End Stack

- Continue using React, but:
  - Use the `create-react-app` toolchain which gives us Jest, eslint, HMR, and more out of the box
  - Use Typescript over Proptypes for more strict typing
  - Use GraphQL for API calls and `apollo-client-cache` for global state management
  - Use `reach-router` instead of `react-router`
  - Use directories for components instead of filenames
    - The Storybook and test file will live adjacent to the component `index.tsx` file which will allow all associated component files to live in the same directory and makes imports shorter.
    - Keep images inside of the component directory where used until they need to be shared across multiple components
    - Maintain a flat `src/components/` directory structure for easy imports and file finding, preferring a `NounDescriptor` naming approach to keep similar files together in the tree, such as `PageExperimentForm/` and `PageExperimentDetails/`
- Continue using Bootstrap (Bootstrap CSS core and `react-bootstrap`), but:
  - Add stylelint for SCSS linting overrides and document that any custom overrides should be kept very minimal
  - Use breakpoints established in FxA
- Utilize Storybook for browsing the UI in various states without running the stack
- Add Sentry to catch client-side errors

## Considered Alternatives

- Further front-end and back-end directory tree separation with `app/client/` and `app/server/` directories
- Refactor existing `rapid` project rather than use CRA for `nimbus-ui`
- Use existing API calls instead of switching to GQL
- Use Tailwind instead of Bootstrap

### Positive Consequences

Building the front-end application inside of `app/experimenter/nimbus-ui` and moving the `core` application and templates into `app/experimenter/legacy/legacy-ui` allows for better separation of concerns (front-end/back-end, legacy/Nimbus front-end code) while continuing to serve the front-end inside of the Django application. Continuing to use React and Bootstrap while starting a new app with `create-react-app` and GraphQL/Apollo allows us to benefit from stack and tooling improvements while avoiding an entire rewrite of all front-end components.

Some members of the FxA team are rolling off of a React/GQL project, `fxa-settings`, with a similar front-end stack and [good documentation](https://github.com/mozilla/fxa/tree/main/packages/fxa-settings). This project can be referenced for using CRA, Storybook examples, how to set up and use the apollo cache, testing helpers, and testing examples using GQL queries and mutations.

### Negative Consequences

This approach for `nimbus-ui` will require time to reach parity to the current `rapid` project.

## Pros and Cons of the Considered Alternatives

### Further FE and BE separation

The team considered further isolating the front-end and back-end with a more top-level separation, taking `app/experimenter/nimbus-ui/` proposed in this ADR and placing it instead in `app/client/`, with the back-end moving from `app/experimenter/` to `app/server/experimenter/`. Since the React application would then live outside the top-level Django, we would need to serve the front-end with nginx and several changes would need to be made for local dev and production.

At the time of writing, this has been decided against due to additional set up time required, but could potentially be done at a later time. [See the discussion held here](https://github.com/mozilla/experimenter/pull/3392#discussion_r485063856) for more details.

### Refactor existing project

- Pros
  - Less time spent on new project scaffolding
- Cons
  - Because the `rapid` project is small, this may cause points of frustration and more time than expected shuffling files around, refactoring, modifying tests, and reconnecting the pieces with a new global state management approach compared to starting anew
  - We desire to use the build pipeline offered and managed by `create-react-app` regardless (see [FxA's React Toolchain ADR](https://github.com/mozilla/fxa/blob/main/docs/adr/0013-react-toolchain-for-settings-redesign.md)) and it may be awkward porting an existing application over
  - Refactoring instead of "starting fresh" provides a weaker sense of collective ownership from new contributors and excitement for fresh perspectives

### Don't use GQL

- Pros
  - Less additional work on the front-end and back-end initially
  - Non-FxA engineers would likely experience a learning curve switching to GQL
- Cons
  - As the application grows, we will likely need to set up Redux or grow the current ad-hoc global state management
  - We won't reap the benefits of a GQL application (see [FxA's GQL ADR](https://github.com/mozilla/fxa/blob/main/docs/adr/0016-use-graphql-and-apollo-for-settings-redesign.md)) such as reduced network requests and data transferred, clarity around expected data and server responses, client-side caching and global state management via `apollo-client-cache`, helpful developer tooling, potentially [GQL subscriptions](https://www.apollographql.com/docs/react/data/subscriptions/), and speedier development in the long run

### Use Tailwind instead of Bootstrap

- Bootstrap
  - Pros
    - Offers a complete UI kit/library to aid in accelerated component styling, leading to less time spent on a custom UI and less time needed on style polishing
    - Is already being used in the `rapid` project, leading to less component refactoring. With a new `nimbus-ui` application, bits and pieces can likely be copied over
  - Cons
    - Isn’t being used in FxA and prevents any potential React component sharing down the line with FxA if we make `fxa-react` more widely available
    - Is another CSS framework and style pattern for newcomers to pick up on and has a steeper learning curve than other CSS solutions because it offers more
    - Is a little bulky - we won’t use everything it offers, but this is a much less important consideration for an internal tool like Nimbus
    - Lacks customization options without forking our own copy or adding style overrides
- Tailwind
  - Pros
    - Has already been setup in `fxa-admin-panel`, `fxa-settings`, and `fxa-react`, meaning 1) it should be straightforward to setup in Nimbus and 2) gives us an option to potentially share React components with FxA (if we make `fxa-react` more widely available)
    - Developers using it in FxA have given positive feedback on its ease of use
    - `fxa-settings` has a design guide available for reference and docs written for FxA styling component conventions
    - Allows us more flexibility without overriding styles on what the overall visual design of the UI will end up as
  - Cons
    - Non-FxA engineers may need to ramp up since the `rapid` project is currently using Bootstrap
    - Will require significant refactoring from what already exists in the `rapid` project
    - Is a much less complete solution than Bootstrap/`react-bootstrap`, leading to much more time spent on custom UI classes and our own form components

Ultimately, Bootstrap was chosen to stick around because Bootstrap CSS and `react-bootstrap` offer a lot of form (and other) components and styles out of the box and the "development speed" decision driver holds significant weight for this project.

## Links

[ADR #0001](https://github.com/mozilla/experimenter/blob/main/app/experimenter/docs/adrs/0001-build-nimbus-console-in-experimenter.md) - documented decision to build Nimbus in this repository with the existing Django back-end\
[graphene-django](https://github.com/graphql-python/graphene-django) - package to allow GraphQL in Python/Django\
[FxA Settings README](https://github.com/mozilla/fxa/tree/main/packages/fxa-settings) - well-documented project with a similar front-end stack that can be referenced for examples with other relevant ADRs (GQL, React Toolchain) linked at the top
