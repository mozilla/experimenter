# Mozilla Experimenter Nimbus UI

## Development

- `yarn start` to start the app in development mode on `http://localhost:3000`
- `yarn build` to create a production build
- `yarn test` to run unit tests, coverage details are displayed by default

## App Configuration

Nimbus uses two approaches for retrieving configuration:

#### Template-rendered configuration

This is used to ensure critical information about the app is retrieved and made available immediately. These details are encoded and rendered in the HTML when the main [Django template](../legacy-ui/templates/experiments/nimbus-ui.html) for loading `nimbus-ui` is requested, and are subsequently parsed by the React app when it is initialized.

The values for this configuration are defined in the [`APP_CONFIG`](../base/context_processors.py) custom context processor.

Accessing these configuration values in the React app is simple: just import the `config` object and access its properties. Example:

```ts
import config from "./lib/config";
console.log(config.sentry_dsn);
```

#### GraphQL configuration

TODO: someone who knows more about this than me should fill this out.

## Overriding Webpack defaults

This React app uses `create-react-react`, which famously provides sensible defaults and is incredibly easy to get off the ground. With this also comes the restriction that you can't modify the Webpack configuration - and for good reason! The setup of CRA under the hood is complex and somewhat fragile, so it's for our own protection.

Except, we know what we're doing. And because we _do_ want all the benefits of CRA with a few small modifications, this app also uses [Rescripts](https://github.com/harrysolovay/rescripts).

You can read up over on their page if you want to know all the details, but if you're looking to make changes to CRA's Webpack configuration, you can do so inside [`.rescriptsrc.js`](.rescriptsrc.js). Rescripts will consume each exported item from this file, supplying it the full config as a function argument, and expecting the modified config back in return.

## Testing

This package uses [Jest](https://jestjs.io/) to test its code. By default `yarn test` will test all JS/TS files under `src/`.

Test specific tests with the following commands:

```bash
# Test for the component AppLayout
yarn test AppLayout

# Grep for "renders as expected"
yarn test -t="renders as expected"

# See a full code coverage report
yarn test --watchAll=false
```

Refer to Jest's [CLI documentation](https://jestjs.io/docs/en/cli) for more advanced test configuration.

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
