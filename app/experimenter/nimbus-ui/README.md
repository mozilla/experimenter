# Mozilla Experimenter Nimbus UI

## Development

- `yarn start` to start the app in development mode on `http://localhost:3000`
- `yarn build` to create a production build
- `yarn test` to run unit tests, coverage details are displayed by default

## Testing

This package uses [Jest](https://jestjs.io/) to test its code. By default `yarn test` will test all JS/TS files under `src/`.

Test specific tests with the following commands:

```bash
# Test for the component AppLayout
yarn test AppLayout

# Grep for "renders as expected"
yarn test -t="renders as expected"
```

Refer to Jest's [CLI documentation](https://jestjs.io/docs/en/cli) for more advanced test configuration.

## Storybook

This project uses [Storybook](https://storybook.js.org/) to visually show each component and page of this project in various application states without requiring the full stack to run.

In local development, `yarn storybook` will start a Storybook server at <http://localhost:3001> with hot module replacement to reflect live changes. We plan to push Storybook builds from pull requests and commits to a GH pages URL in the very near future.

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
    <Alert variant="danger">
      This is a Danger alert!
    </Alert>
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

## License

MPL-2.0
