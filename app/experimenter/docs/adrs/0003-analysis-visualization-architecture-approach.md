# Analysis Visualization: Architecture Approach

* Status: accepted
* Deciders: Marina Samuel, Jared Lockhart, Kate Hudson
* Date: 2020-09-16

## Context and Problem Statement

Analysis and visualization of experiment result data needs to be [part of the experiment console](https://github.com/mozilla/nimbus-shared/blob/main/docs/adr/0001-one-console-app.md). The mockups based on user interviews are [here](https://www.figma.com/file/5SLa07XqQb0ttB1ay1gami/Nimbus-Console-UI).

Some decisions need to be made about how the data will be pulled out of [Jetstream](https://github.com/mozilla/jetstream) and visualized within the console. This ADR will highlight how this will be done.


## Decision Drivers

Drivers for fetching data:
* Data is easy to fetch and minimizes the amount of new state added

Drivers for visualizing data:
* Reuse existing [Graph Paper](https://github.com/graph-paper-org/graph-paper) UI components if possible
* How easy or possible is it to integrate Svelte components into React (since Graph Paper is in Svelte)


## Considered Options

**Fetching Data**
1. Add a POST endpoint to Experiment Console to send data over from Jetstream. This data would be saved in the Django database and fetched from the front-end when needed using GraphQL.
2. The visualization front end fetches data via a Django REST API, which fetches Jetstream data on demand using GCS dependencies. Data is not stored in the database.

**Frontend**
1. Use nvd3 or other graphing library as an alternative to Graph Paper
2. Use Graph Paper/Svelte only for graphs, otherwise, all visualizations from the mockup will be in React
3. Use Svelte for the entire visualization portion of the console

## Decision Outcome

**Fetching Data**
Option (2) was chosen.

While option (2) requires adding more state such as bucket credentials, it is more straight-forward than option (1). It does not require any changes on the Jetstream side to make POST calls. It also does not require storing the data to the Django database. This is ok since the aggregated data is very small, in the range of around 100kb per fetch. Additionally, giving write access to Jetstream would also change the authentication requirements for it and may require a security review.

It is worth noting that there will be no caching layer to start since the response seems to be fairly quick. However, in the future, if we start sending more data or observe any slowness, we can consider adding cachine.

**Frontend**
Option (2) was chosen. At a high level, this would look like:
1. From within the React application, per experiment result page, in one REST API call, send the experiment slug.
2. Receive all visualization data for that experiment (will include multiple graphs).
3. Take that data and feed it into already-existing Svlete components for display
Note that the existing Graph Paper components are not comprehensive, so some additional code will be written in Svelte to piece together and use the Graph Paper components.

Option (1) is not ideal since existing libraries would be less customizable than our in-house library that we have already invested in.  The only reason to have chosen this was if it was not possible to embed Svelte in React. However, this has been proven to be possible. The method that has been shown to work looks like:
1. Add init() function hooks in the Svelte code where data and a DOM node can be passed in.
2. Create a bundle.js for the Svelte package
3. Include the bundle in the React code and call the init() function, passing in a DOM node to render in and data required for graphs.

Option (3) has the benefit of keeping the entire visualization component separated and written in the same language. The main issue with this is that, given the mockups, some portions of the mockups may be reused in other parts of the console (e.g. the overview table). So they should be available in React.
Furthermore, the only reason for using Svelte is for graphing purposes. It would be best to stick with same conventions/standard of using React wherever possible within the codebase.