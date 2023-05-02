# Cirrus Server to get Feature configuration API structure

This Cirrus API allows clients to obtain a set of features based on their provided `client_id` and context information.

## Endpoint

`POST /v1/features/`

## Input

The input should be a JSON object with the following properties:

- `client_id` (string): Used for bucketing calculation.
- `context` (object): Used for context. It has the following properties:
  - `locale` (string): The locale for the user.
  - `user` (object): The user object has the following properties:
    - `is_premium` (bool): Indicates if the user is a premium user.
    - `session_id` (string): The session ID for the user.

Example input:

```json
{
  "client_id": "4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449",
  "context": {
    "locale": "en-US",
    "user": {
      "is_premium": true,
      "session_id": "f1a987754824be035f349b0809b731d3"
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
  "features": {
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
}
```

## Notes

- This API only accepts POST requests.
- All parameters should be supplied in the body as JSON.
