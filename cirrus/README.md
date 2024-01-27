# Cirrus

Cirrus is a feature configuration server that allows clients to obtain a set of features based on their provided `client_id` and `context` information.
This document provides information on setting up the Cirrus environment, including required environment variables and commands for running and testing Cirrus.

## Environment Setup

To set up the Cirrus environment, follow these steps:

1. Create a `.env` file inside the `cirrus/server` directory.
2. Copy the contents of `.env.example` into `.env` by running the following command:

   ```bash
   cp .env.example .env
   ```

3. Open the `.env` file and modify the values of the following environment variables:

   ```plaintext
   CIRRUS_REMOTE_SETTING_URL=https://firefox.settings.services.mozilla.com/v1/buckets/main/collections/nimbus-web-experiments/records
   CIRRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS=10
   CIRRUS_APP_ID=test_app_id
   CIRRUS_APP_NAME=test_app_name
   CIRRUS_CHANNEL=developer
   CIRRUS_FML_PATH=./feature_manifest/sample.fml.yaml
   CIRRUS_SENTRY_DSN=dsn_url
   CIRRUS_INSTANCE_NAME=cirrus_pod_app_v1
   CIRRUS_ENV_NAME=test_app_stage
   CIRRUS_GLEAN_MAX_EVENTS_BUFFER=10

   ```

   Here's what each variable represents:

   - `CIRRUS_REMOTE_SETTING_URL`: The URL of the remote settings where the experiments data is stored. In this case, it points to the collection of nimbus web experiments.
   - `CIRRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS`: The refresh rate in seconds for fetching the experiments recipes from the remote settings. Set it to `10` to retrieve the latest data every 10 seconds.
   - `CIRRUS_APP_ID`: Replace `test_app_id` with the actual ID of your application for example `firefox-desktop`.
   - `CIRRUS_APP_NAME`: Replace `test_app_name` with the desired name for your application for example `firefox_desktop`.
   - `CIRRUS_CHANNEL`: Replace `developer` with the channel like `beta`, `release` etc.
   - `CIRRUS_FML_PATH`: The file path to the feature manifest file. Set it to `./feature_manifest/sample.fml.yaml` or specify the correct path to your feature manifest file.
   - `CIRRUS_SENTRY_DSN`: Replace `dsn_url` with the appropriate DSN value.
   - `CIRRUS_INSTANCE_NAME`: Replace with the instance name.
   - `CIRRUS_ENV_NAME:` Replace with the concatenation of project and environment name
   - `CIRRUS_GLEAN_MAX_EVENTS_BUFFER`: This value represents the max events buffer size for glean. You can set the value from range 1 to 500, by default Cirrus sets it to 10.

   Adjust the values of these variables according to your specific configuration requirements.

By following these steps, you will create the `.env` file and configure the necessary environment variables for the Cirrus application.

## Commands

The following are the available commands for working with Cirrus:

- **cirrus_build**: Builds the Cirrus container.

  - Usage: `make cirrus_build`

- **cirrus_up**: Starts the Cirrus container.

  - Usage: `make cirrus_up`

- **cirrus_down**:`cirrus_down`: Stops the Cirrus container.

  - Usage: `make cirrus_down`

- **cirrus_test**: Runs tests for the Cirrus application.

  - Usage: `make cirrus_test`

- **cirrus_check**: Performs various checks on the Cirrus application including Ruff linting, Black code formatting check, Pyright static type checking, pytest tests, and documentation generation.

  - Usage: `make cirrus_check`

- **cirrus_code_format**: Formats the code in the Cirrus application.

  - Usage: `make cirrus_code_format`

- **cirrus_typecheck_createstub**: Performs static type checking and creates stub files.

  - Usage: `make cirrus_typecheck_createstub`

- **cirrus_generate_docs**: Generates documentation for the Cirrus application such as openapi schema.
  - Usage: `make cirrus_generate_docs`

## OpenAPI Schema

[OpenAPI schema](/cirrus/server/cirrus/docs/openapi.json) for the Cirrus API

# Cirrus Server to get Feature configuration API structure

## Api Doc

[Cirrus Api Doc](/cirrus/server/cirrus/docs/apidoc.html) for the Cirrus API

## Endpoint

`POST /v1/features/`

- When making a POST request, please make sure to set headers content type as JSON
  ```javascript
    headers: {
            "Content-Type": "application/json",
      }
  ```

## Input

The input should be a JSON object with the following properties:

- `client_id` (string): Used for bucketing calculation.
- `context` (object): Used for context. It can have any key-value pair.
  - `any-key` (anytype).

Note: Make sure to provide a key-value pair when making a call, setting the `context` value as `{}` will be considered as `False` value. For testing you can set value such as
```json
 context: { key: "example-key" }
```
Example input:

```json
{
  "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
  "context": {
    "key1": "value1",
    "key2": {
      "key2.1": "value2",
      "key2.2": "value3"
    }
  }
}
```

## Output

The output will be a JSON object with the following properties:

- `features` (object): An object that contains the set of features. Each feature is represented as a sub-object with its own set of variables.

Example output:

```json
{
  "Feature1": {
    "Variable1.1": "valueA",
    "Variable1.2": "valueB"
  },
  "Feature2": {
    "Variable2.1": "valueC",
    "Variable2.2": "valueD"
  },
  "FeatureN": {
    "VariableN.1": "valueX",
    "VariableN.2": "valueY"
  }
}
```

## Notes

- This API only accepts POST requests.
- All parameters should be supplied in the body as JSON.
