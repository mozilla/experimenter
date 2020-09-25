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

## License

MPL-2.0
