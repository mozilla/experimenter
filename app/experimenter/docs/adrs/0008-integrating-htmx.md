# Front-end web development with HTMX

- Status: accepted
- Deciders: Yashika Khurana, Jared Lockhart, Elise Richards
- Date: 2022-10-25

## Context and Problem Statement

Nimbus UI uses GraphQL to fetch data from the backend and it highly depends on the three packages i.e. [graphene-django](https://github.com/graphql-python/graphene-django), [graphene](https://github.com/graphql-python/graphene) and [apollo-client](https://github.com/apollographql/apollo-client) and we have seen these packages not getting released new versions for a while. We have found out that using GraphQL significantly hinders the performance of the Experimenter as it adds extra overhead while making the call and the benefit of using GraphQL is not something we are making use of. We also have to significantly maintain the burden to implement most of the API in both DRF (Django Rest Framework) and GraphQL, and additional testing and tools are required to support that. As our application is growing so what steps we should take to improve the performance and better maintainability of the application?

## Decision Drivers

- Improve performance which leads to better UX Experience
- Reduce dependency on extra packages
- Better easier development tooling
- Better maintainability of the application

## Considered Options

- Get rid of GraphQL and transition to REST Api's and keeping the Typescript/React frontend
- Designing new pages with HTMX, and keep the existing UI (React and GraphQL) and eventually move to HTMX

## Decision Outcome

Chosen option: After careful consideration, we have decided to choose the option - Designing new pages with HTMX, and keep the existing UI (React and GraphQL), and eventually moving to HTMX. Moving to HTMX is simpler in terms of backend compatibility as we can use our existing code without any major modifications. Work includes creating new pages using HTMX, setting up test cases to test HTMX pages, and evaluating the success/failure of HTMX on the Experimenter platform, so that if we are successful we can start the transition from React to HTMX completely. Whereas in option 1 we need to actively work on the backend and frontend to transit from GraphQL to REST Apis. This can only work once we have converted everything to Rest Api's i.e. both frontend and backend. Particular V5 API of the experimenter is not used anywhere else apart from the front end, so if we switch to HTMX, we will be not dependent on any kind of APIs and will be closer to the server. The main benefit of choosing option 2 is that it can co-exist with React/GraphQL, meanwhile, we will update to the latest dependency packages to improve performance and can slowly progress towards 100% HTMX.

### Positive Consequences

- All web pages using HTMX!
- Better performance
- Learn new tool HTMX

### Negative Consequences

- We'd be looking for to determine whether the new pages aren't successful. The one possible solution would be to re-write those pages in Typescript/React and instead of GraphQL and transition to Rest API.

## Pros and Cons of the Options

### Get rid of GraphQL and transition to REST Api's and keeping the Typescript/React frontend

We are currently dependant on the three packages mentioned above to use GraphQL in the project. For the time being (around one year)these packages were not releasing new versions which was one of the major factors of the performance, and recently they released new versions. We are highly dependent on the three packages and not getting the new version for the while worries us. All the API calls are using GraphQL and which increases the response time and decreases the performance of the platform. So the solution is to get rid of GraphQL and use REST API and keep the existing Typescript/React frontend. This requires a lot of work for example changing Nimbus UI GraphQL call to REST API call, modifying frontend test cases and as well integration test cases, supporting backend for Rest API, and changing backend test as well
Pros:

- We can keep using React with Rest Api
- Better performance
- Keep using Jest for the frontend testing frameworks

Cons:

- Rewriting a lot of frontend test cases and frontend queries call
- Writing and maintaining APIs which will be not used anywhere other than frontend

### Designing new pages with HTMX, and keep the existing UI (React and GraphQL) and eventually move to HTMX

In this approach we will be aiming to develop new pages with HTMX and keeping the existing pages in React (with GraphQL). It doesn't make sense to first change GraphQL to Rest API and then get rid of REST APIs too as we don't need any kind of API to use HTMX. Django has good support for HTMX and it avoids network overhead too. So to save time we can avoid the transition of GraphQL to Rest API and keep the GraphQL and start developing new pages in HTMX. We can keep the HTMX and React at the moment, and can slowly start the transition of pages from React to HTMX.
Pros:

- Don't need JEST framework for frontend testing
- Easy HTMX testing
- Better performance
- Hybrid HTMX and React architecture enables incremental changes
- HTMX-Very small library (9kB) compared to the React framework
- Feel like no javascript to write, more python focused
- Improved maintainability
- Lower testing surface
- Fewer package dependencies
- No API's call needed
- We can consider using [Tailwind](https://tailwindcss.com/) instead of Bootstrap

Cons:

- New framework, involves little learning curve
- Need to set up testing for HTMX pages
- Can create complexity during the transition between React and HTMX
- Complex user interactions might be more difficult (like if we want interactive data visualizations on the Results page)

## Links

- [HTMX](https://htmx.org/)
