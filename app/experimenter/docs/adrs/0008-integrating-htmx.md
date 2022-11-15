# Front-end web development with HTMX

- Status: accepted

- Deciders: Yashika Khurana, Jared Lockhart, Elise Richards <!-- optional -->

- Date: 2022-10-25 <!-- optional -->

## Context and Problem Statement

[Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question.]

Nimbus UI uses GraphQL to fetch data from the backend and it highly depends on the two packages i.e. [graphene-django](https://github.com/graphql-python/graphene-django) and [graphene](https://github.com/graphql-python/graphene). We have found out that using GraphQL significantly hinders the performance of the Experimenter as it adds extra overhead while making the call. As our application is growing so what steps we should take to improve the performance and better maintainbility of the application?

<!-- So we want to start building webpages in HTMX to avoid dependency between the React, GraphQL and the additional packages required.

Since we have new feature coming up to allow user to creat new rollout which requires setting up new pages, we will be building those related pages in HTMX and will have hybrid frontend at the moment i.e. React and HTMX. Once we measure the success/failure of HTMX, we can decide to transition our Nimbus UI from React to HTMX completely. -->

## Decision Drivers <!-- optional -->

- Improve performance which leads to better UX Experience

- Dependency of using extra packages

## Considered Options

- Get rid of GraphQL and transition to REST Api's

- Designing new pages with HTMX, and keep the exisiting UI (React and GraphQL) and eventually move to HTMX

## Decision Outcome

Chosen option: After careful considerations, we have decided to choose option - Designing new pages with HTMX, and keep the exisiting UI (React and GraphQL) and eventually move to HTMX. This include creating new pages using HTMX, setting up test cases to test hmtx pages and evaluating the success/failure of HTMX on the Experimenter platform, so that if we are successful we can start transition from React to HTMX completely.

[justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

### Positive Consequences <!-- optional -->

- All web pages using HTMX!
- Better performance
- Learn new tool HTMX

### Negative Consequences <!-- optional -->

- If new pages didn't succeed, we need to re-write those pages in React and instead of GraphQL we will be working on transition to Rest API

## Pros and Cons of the Options <!-- optional -->

### Get rid of GraphQL and transition to REST Api's

[example | description | pointer to more information | …] <!-- optional -->

We are currenlty dependant on the two packages mentioned above to use GraphQL in the project. For the time being (around one year)these packages were not releasing new versions, and recently they released new versions. We are highly dependent on the two packages and not getting the new version for the while worry us. All the API calls are using GraphQL and it increases the response time and decreases the performance of the platform. So the solution is to get rid of GraphQL and use REST API. This requires a lot of work for example changing Nimbus UI graphql call to REST API call, modify frontend test cases and as well as integration test cases, supporting backend for Rest API and changing backend test as well

Pros: - We can keep using React with Rest Api - Increase in performance - Keep using Jest for the frontend testing framework

Cons:

- Rewritting lot of frontend test cases and frontend queries call

- Good, because [argument a]

- Good, because [argument b]

- Bad, because [argument c]

- … <!-- numbers of pros and cons can vary -->

### Designing new pages with HTMX, and keep the exisiting UI (React and GraphQL) and eventually move to HTMX

We will be aiming to develop new pages with HTMX and keeping the exisitng pages in React (with GraphQL). It doesn't make sense to first change GraphQL to Rest Api and then getting rid of REST APIs too as we don't need any kind of API to use HTMX and Django have a good support for HTMX and it avoids network overhead too. So to save our time we can avoid transition of GraphQL to Rest API and keep the GraphQL and start developing new pages in HTMX. We can keep the HTMX and React at the moment, and can slowly start the transition of pages from React to HTMX

[example | description | pointer to more information | …] <!-- optional -->

Pros:

- Don't need JEST framework for frontend testing

- Easy htmx testing

- Better performance

- Hybrid HTMX and React architecture

- More close to python
- HTMX-Very small library (9kB) compared to the React framework

- No javascript to write, more python focused

- No API's call needed

Cons:

- New framwork, involves little learning curve

- Need to set up testing for HTMX pages

- Can create complexity during transition between React and HTMX

## Links <!-- optional -->

- [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->

- … <!-- numbers of links can vary -->
