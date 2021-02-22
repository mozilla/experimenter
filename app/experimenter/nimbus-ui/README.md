# Mozilla Experimenter Nimbus UI

## Development

- `yarn start` to start the app in development mode on `http://localhost:3000` (alternatively, run `make up` at the project root and navigate to `localhost/nimbus`)
- `yarn build` to create a production build
- `yarn test` to run unit tests, coverage details are displayed by default

## App Configuration

Nimbus has two types of config available within the app: template-rendered and GraphQL.

#### GraphQL configuration (preferred method)

This is configuration information that the app loads from the server via GraphQL request when the app first starts. This information is stored in the Apollo cache and is made available via the `useConfig` hook, where properties can be destructured out. Conveniently, this hook also includes the template-rendered configuration properties described below, making it the preferred option for both types of config.

Usage is simple:

```ts
import useConfig from "./hooks/useConfig";

// channels and probesets come from GraphQL, sentry_dsn
// comes from initial template-rendered config
const { channels, probeSets, sentry_dsn } = useConfig();
```

The query for GraphQL config is performed inside the `<App>` component, which makes it immediately available (no need to check for loading) in any child components.

#### Template-rendered configuration

This is used to ensure critical information about the app is retrieved and made available immediately. These details are encoded and rendered in the HTML when the main [Django template](../legacy-ui/templates/experiments/nimbus-ui.html) for loading `nimbus-ui` is requested, and are subsequently parsed by the React app when it is initialized.

The values for this configuration are defined in the [`APP_CONFIG`](../base/context_processors.py) custom context processor.

Accessing these configuration values in the React app is simple: just import the default `./lib/config` object and access its properties. Example:

```ts
import config from "./lib/config";
console.log(config.sentry_dsn);
```

## Overriding Webpack defaults

This React app uses `create-react-react`, which famously provides sensible defaults and is incredibly easy to get off the ground. With this also comes the restriction that you can't modify the Webpack configuration - and for good reason! The setup of CRA under the hood is complex and somewhat fragile, so it's for our own protection.

Except, we know what we're doing. And because we _do_ want all the benefits of CRA with a few small modifications, this app also uses [Rescripts](https://github.com/harrysolovay/rescripts).

You can read up over on their page if you want to know all the details, but if you're looking to make changes to CRA's Webpack configuration, you can do so inside [`.rescriptsrc.js`](.rescriptsrc.js). Rescripts will consume each exported item from this file, supplying it the full config as a function argument, and expecting the modified config back in return.

## Accessing GraphQL Type Definitions

All of our GraphQL resolvers produce types that are compatible with TypeScript, so there is no need to write new types for the queries you perform with Apollo.

To generate types, just run `yarn generate-types`. This will generate type declarations inside a `types/` directory at the root of this app. Once generated you can import and use as you see fit. If there are changes to the graphql API on the server, run `make generate_types` to export the server schema and update the typescript stubs.

For example, a query that looks like this:

```ts
export const GET_EXPERIMENT_OVERVIEWS = gql`
  query GetExperimentOverviews {
    experiments {
      name
      slug
      hypothesis
    }
  }
`;
```

Would be analyzed and the corresponding types generated would look like this:

```ts
export interface GetExperimentOverviews_experiments {
  name: string;
  slug: string;
  hypothesis: string | null;
}

export interface GetExperimentOverviews {
  /**
   * List Nimbus Experiments.
   */
  experiments: (GetExperimentOverviews_experiments | null)[] | null;
}
```

## Error handling

Note: see the "Forms and Validation" section for form-specific error handling.

This app has an [`AppErrorBoundary`](./src/components/AppErrorBoundary/index.tsx) that will capture any uncaught error that occurs and report them to Sentry. This acts as our last line of defense, but ideally we are able to handle errors before they get to this stage. As well, errors that we wish to display to the user should generally be handled in a consistent fashion.

### General errors

General errors can occur when an operation fails altogether. This could be for any reason, such as when a network request fails, or a bad code path raises an exception. For these errors you'll use React Bootstrap's [`Alert`](https://react-bootstrap.github.io/components/alerts/) components.

For example, if error occurs while saving a record:

```tsx
<Alert variant="warning">Sorry, there was a problem.</Alert>
```

_Note:_ displaying technical error messages to the user may not be very helpful, so it's generally advised to either provide a [generic message](./src/lib/constants.ts) or instructions on what to do.

### Handling GraphQL operation errors

As GQL queries and mutations are how we get data in and out of the app this is where a majority of our errors are going to occur. These should be handled in a consistent fashion as well.

Both operations can result in a general error, such as a `NetworkError`, or GraphQL errors, which in most cases will be validation errors. Importantly, these two types of errors occur in different ways; general errors will throw or trigger the operations `onError` function, and GraphQL errors will be present in the result of the operation.

At this time we're not requiring any errors to be reported to Sentry as uncaught client errors will bubble up to `AppErrorBoundary`, we don't want to report validation errors, and true GraphQL server errors are already reported on the server-side.

An example of handling a `useMutation` operation:

```tsx
// Set up the Mutation
const [updateSomething] = useMutation(UPDATE_RECORD_MUTATION);

// Later, execute it.
try {
  const result = await updateSomething({
    variables,
  });

  if (!result.data?.updateSomething) {
    throw new Error("Update failed for an unknown reason");
  }

  const { message, record } = result.data.updateSomething;

  // In our GraphQL response, the `data.message` could be "success"
  // to indicate successful mutation, another error string, or an
  // object containing field keys and an array of string errors.
  if (message !== "success" && typeof message === "object") {
    console.log("A GraphQL error occurred", message);
    return;
  }

  console.log("Record updated", record);
} catch (error) {
  console.log("A general error occurred", error.message);
}
```

An example of handling a `useQuery` operation:

```tsx
// Set up the query, and because it executes immediately, handle it
// immediately by passing in an `onError` option. This is the same as
// wrapping it in a try/catch, just a little more grouped together.
const { data } = useQuery(GET_RECORD_QUERY, {
  onError(error) {
    console.log("A general error occurred", error.message);
  },
});

const { message, record } = data.getRecord;

// Less likely with a query, but still check for GQL errors
if (message !== "success") {
  console.log("A GraphQL error occurred", message);
  return;
}

console.log("Retrieved record", record);
```

## Forms and Validation

**See the form validation section of [Storybook](https://storage.googleapis.com/mozilla-storybooks-experimenter/index.html) for examples and a visual guide to the UX interaction.**

There are three kinds of validation that need to be applied to forms: client-side, server-side, and "required for launch".

### `useCommonForm` and `useCommonNestedForm`

All forms use [`react-bootstrap`](https://react-bootstrap.github.io/components/forms/) as well as the custom convenience hooks `useCommonForm` or `useCommonNestedForm` for ease of use when developing new forms, to promote consistent behavior amongst our forms, and to limit any future changes affecting all forms in limited places. These hooks utilize the [`react-hook-form`](https://react-hook-form.com/api) package.

If there are no nested forms, pass the needed parameters into `useCommonForm`. Otherwise, pull form methods out of _our_ `useForm` hook and pass them into `FormContext`. Then, in the nested form(s), pull out the methods and pass them into `useCommonNestedForm`.

Server errors occur when a user attempts to create or modify a record and the server rejects the request. We surface client-side errors to prevent invalid mutations from being attempted and to give users instant feedback if we know a field is invalid. For non-field server-side errors, refer to the "General Errors" section above.

Both hooks return a `FormErrors` JSX Element, intended for use on every form field, which will display client-side errors, server-side errors, or both, within React Bootstrap's [`Form.Control.Feedback`](https://react-bootstrap.github.io/components/forms/#form-control-feedback-props).

Both hooks also return a form control method that returns an object containing field attributes that should be spread onto the form control or select (`formControlAttrs`).

A basic example of a form field utilizing `useCommonForm`:

```
<Form.Group controlId="name">
  <Form.Label>Public name</Form.Label>
  <Form.Control
    {...formControlAttrs("name")}
    type="text"
  />
  <FormErrors name="name" />
</Form.Group>
```

#### Client-side validation rules

Form fields are optional by default - that is, users can save pieces of the experiment without filling in every input on the page. To enforce a required field or client-side validation on the field, pass a rule into the method...

```
{...formControlAttrs("hypothesis", REQUIRED_FIELD)}
```

```
{...formControlAttrs("populationPercent", NUMBER_FIELD)}
```

... where the rule is a [`registerOptions`](https://react-hook-form.com/ts#RegisterOptions) object that can set the validation via handy properties like `maxLength`, and/or a `validate` function that can match a regex pattern or provide custom validation.

Allow this argument to handle and dictate the client-side validation because we can (and should) display an error message to the user with it. Enforcing validation with `type` etc. can lead to invalid/red fields without a message for the user.

#### Multiselects

Multiselects use the hooks similarly, but because the `Select` element comes from the [`react-select`](https://react-select.com) package, the behavior is slightly different. Use and spread the object returned by `formSelectAttrs` provided by our hooks instead and use `FormErrors` identically.

```
<Form.Group
  controlId="multi"
  >
  <Form.Label>Multi</Form.Label>
    <Select
      isMulti
      {...formSelectAttrs("multi")}
      options={arrayOfStringOptions}
    />
  <FormErrors name="multi" />
</Form.Group>
```

### Required for Launch Validation

Some fields like `publicDescription` are allowed to be `null` while someone is editing a draft, but must be set before the experiment can move to the `review` status. You should NOT mark these fields `required`, but rather add help text that indicates they must be filled out before launch.

## Access Visualization Data Locally

The Results page renders experiment analysis data and can only be accessed when an experiment is complete, the analysis feature flag is on, and the analysis data returned from the visualization API endpoint is available.

To see the Results page and data locally:

1. Ensure your [Google Credentials](https://github.com/mozilla/experimenter#google-credentials) are configured
2. Set `FEATURE_ANALYSIS=true` in your local `.env` file
3. Create a Nimbus Experiment at `localhost/admin` with experiment slug "testing-nimbus" status "complete," a branch/branch slug named "control", and another branch/branch slug named "treatment". Alternately, change an existing, complete Nimbus experiment with branches in place to reflect the experiment slug `testing-nimbus`.

## Testing and Mocking

This package uses [Jest](https://jestjs.io/) to test its code. By default `yarn test` will test all JS/TS files under `src/`.

Test specific tests with the following commands:

```bash
# Test for the component AppLayout
yarn test AppLayout

# Grep for "renders as expected"
yarn test -t="renders as expected"

# See a full code coverage report
yarn test --watchAll=false

# Our tests require 100% line coverage, which can be checked with
yarn test:cov

# Or, if you want to test and get coverage for a specific test
# This excludes Storybook stories while running coverage on a specific component
yarn test:cov --collectCoverageFrom='./src/components/LinkExternal/*[!.stories].tsx' LinkExternal
```

Refer to Jest's [CLI documentation](https://jestjs.io/docs/en/cli) for more advanced test configuration.

### Components that need a GQL Mock

[MockedCache](./src/services/mocks.tsx) is a convenient way to test components that make use of GraphQL mutations. Use it in place of [MockedProvider](https://www.apollographql.com/docs/react/api/react/testing/#mockedprovider) without prop overrides to use the default mocked cache, or pass in `config` to override pieces of the GraphQL config in the default mocked cache. A `mocks` prop can also be passed in when a query or mutation needs success or failure mocks.

Example:

```tsx
const mocks = [];
<MockedCache
  config={{
    channels: [
      {
        label: "Foo Beta",
        value: "FOO_BETA",
      },
      {
        label: "Bar Nightly",
        value: "BAR_NIGHTLY",
      },
    ],
  }}
  {...{ mocks }}
>
  <ExperimentsDirectory />
</MockedCache>;
```

### Mocking mutation errors

Testing for GQL and network errors is also pretty straightforward. In your tests, wrap your component in a `MockedCache` and provide it with mock mutations that produce either an array of `GraphQLError`s, or a standard `Error`. Example with both:

```tsx
const mocks = [
  {
    request: {
      query: GET_EXPERIMENT_OVERVIEW,
      variables: { slug: "foo" },
    },
    result: {
      errors: [new GraphQLError("invalid slug")],
    },
  },
  {
    request: {
      query: GET_EXPERIMENT_OVERVIEW,
      variables: { slug: "foo" },
    },
    error: new Error("network error"),
  },
];

renderWithRouter(
  <MockedCache {...{ mocks }}>
    <ExperimentsDirectory {...{ onDismiss, onError }} />
  </MockedCache>,
);
```

### Simulating GQL query responses in stories & tests

The `MockedCache` component is good for asserting expected GQL requests in tests. But, it doesn't accommodate arbitrary user input - e.g. filling out a form in a Storybook story with random values to try out the UI.

So, we also have [`SimulatedMockLink`](./src/services/mocks.tsx) for use with `MockedProvider` which allows the definition of a function that receives a GQL Operation and can implement a mocked implementation of what happens server-side.

An example of usage can be found in a story like [`basic` for `PageNew`](./src/components/PageNew/index.stories.tsx) - it looks like this:

```tsx
const actionCreateExperiment = action("createExperiment");

const mkSimulatedQueries = ({
  message = "success" as string | Record<string, any>,
  status = 200,
  nimbusExperiment = { slug: "foo-bar-baz" },
} = {}) => [
  {
    request: {
      query: CREATE_EXPERIMENT_MUTATION,
    },
    delay: 1000,
    result: (operation: Operation) => {
      const { name, application, hypothesis } = operation.variables.input;
      actionCreateExperiment(name, application, hypothesis);
      return {
        data: {
          createExperiment: {
            message,
            status,
            nimbusExperiment,
          },
        },
      };
    },
  },
];

const Subject = ({ simulatedQueries = mkSimulatedQueries() }) => {
  const mockLink = new SimulatedMockLink(simulatedQueries, false);
  return (
    <MockedProvider link={mockLink}>
      <PageNew />
    </MockedProvider>
  );
};
```

## Storybook

This project uses [Storybook](https://storybook.js.org/) to visually show each component and page of this project in various application states without requiring the full stack to run.

In local development, `yarn storybook` will start a Storybook server at <http://localhost:3001> with hot module replacement to reflect live changes.

For Pull Requests to the mozilla/experimenter repository on GitHub, Storybook builds [are published to a static website][storybook-builds] via CircleCI test runs. You can view these to see the result of changes without needing to install and run code locally.

The specific build for any given PR or commit should be available as a [status check][status-check] associated with the commit - the check labelled "storybooks: pull request" should have a "details" link for the build.

[storybook-builds]: https://storage.googleapis.com/mozilla-storybooks-experimenter/index.html
[status-check]: https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/about-status-checks

### Linking to Stories

Storybook uses the [withLinks decorator](https://www.npmjs.com/package/@storybook/addon-links#withlinks-decorator) to override default element behavior (using `event.preventDefault()`) and link to a story within Storybook instead.

Add the decorator in the stories for the component that needs to link to another story within Storybook (`.addDecorator(withLinks)`) and simply add `data-sb-kind="StoryName"` to any element in the component to tell Storybook to link to that specific story. The `data-sb-story` attribute is optional as without it Storybook will navigate to the first state in the stories list for that component (usually "basic" or "default"), but can be used to link to a specific state of a story if needed.

## Writing styles

This app uses [Bootstrap v4.5](https://getbootstrap.com/) for styles. There are two ways for you to use it within code:

- [Bootstrap](https://getbootstrap.com/), in other words all the [global styles and classes](https://getbootstrap.com/docs/4.5/layout/overview/) provided by Bootstrap, is available for use without any additional effort. Just write the tags and/or apply the classes you desire.
  - Keep in mind that Bootstrap provides a variety of [utility classes](https://getbootstrap.com/docs/4.5/utilities/borders/) for one-off styles that aren't covered by a component class.
- [`react-bootstrap`](https://react-bootstrap.github.io/) provides us with Bootstrap classes as React components.
  - [Layout components](https://react-bootstrap.github.io/layout/grid/) give access to Bootstrap's grid system for responsively laying out and aligning content. Example:
    ```tsx
    <Container fluid="md">
      <Row>
        <Col>1 of 1</Col>
      </Row>
    </Container>
    ```
  - A [UI component](https://react-bootstrap.github.io/components/alerts/) encapsulates a category of UI, such as a button or alert banner, and tailors how it looks through the props. Example:
    ```tsx
    <Alert variant="danger">This is a Danger alert!</Alert>
    ```

**What about the JavaScript plugins?** While Bootstrap does provide optional JavaScript plugins, they are written in jQuery, which we are decidedly not using in this codebase. You are free to build your own equivalent in vanilla JavaScript or as a React component, or introduce a new package (within reason).

**What about custom CSS?** It's our hope that, with the powerful set of styles offered by Bootstrap paired with TSX, you won't need to write custom CSS. Of course in practice this is not always true, in which case it's advised that you write custom styles in a CSS/SCSS file adjacent to your component. If the custom styles are necessarily global they should be placed in `src/styles/`.

### Customizing Bootstrap

Bootstrap styles are globally introduced in [`src/styles/index.scss`](./src/styles/index.scss), which is then imported into the main app TSX file. Because it's importing Bootstrap's SCSS files you are free to modify its variables and override its imports. For variables it's important to modify them before the import occurs. Example:

```scss
// Modify the "primary" color, used for styling
// buttons and other prominent UI
$theme-colors: (
  "primary": #bada55,
);

// Then import Bootstrap
@import "~bootstrap/scss/bootstrap";
```

Learn more about all the ways you can [theme Bootstrap](https://getbootstrap.com/docs/4.5/getting-started/theming/).

**But Bootstrap supports CSS Variables!** You're right, Bootstrap _does_ support [CSS Variables](https://getbootstrap.com/docs/4.5/getting-started/theming/#css-variables). However, all of those values are rendered out from the variables defined in the SCSS, which we have access to. For this reason, and to avoid unexpected styles, please do not attempt to override any Bootstrap CSS Variables.

## Working with SVGs

Create React App allows us to use SVGs in a variety of ways, right out of the box. We prefer to inline our SVGs where we can:

```javascript
// Inline, full markup:
import { ReactComponent as Logo } from "./logo.svg";
const LogoImage = () => <Logo role="img" aria-label="logo" />;
```

Inlining our SVGs will minimize the number of network requests our application needs to perform. `role="img"` tells screenreaders to refer to this element as an image and `aria-label` acts like `alt` text on an `img` tag does. You can also pass in `className` and other properties, and if needed, conditionally change elements inside of the SVG such as a `path`'s `fill` property.

If the inlined SVG is inside of a button, you can forgo the `role` and `aria-label` by preferring a `title` on a button:

```jsx
import { ReactComponent as CloseIcon } from './close.svg';
...
<button
  title="Close"
>
  <CloseIcon />
</button>
```

Other ways to use SVGs:

```javascript
// As an image source:
import logoUrl from "./logo.svg";
const LogoImage = () => <img src={logoUrl} alt="Logo" />;

// As a background-image (inline style)
import logoUrl from "./logo.svg";
const LogoImage = () => (
  <div
    style={{ backgroundImage: `url(${logoUrl})` }}
    role="img"
    aria-label="logo"
  ></div>
);

// As a background-image (external style)
// Just reference it in CSS, the loader will find it
// .logo { background-image: url('logo.svg'); }
const LogoImage = () => <div class="logo" role="img" aria-label="logo"></div>;
```

## License

MPL-2.0
