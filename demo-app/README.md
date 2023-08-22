# Demo App

This App is designed to test the Cirrus functionality end-to-end.

## Commands available to run the app

- To build the Demo App, including frontend and backend components, use the following command:
  `make build_demo_app`

## Frontend is available at

The frontend of the Demo App is accessible at: [http://localhost:8080](http://localhost:8080)

## Backend is available at

The backend of the Demo App is accessible at: [http://localhost:3002](http://localhost:3002)

## Env config used for the demo app

```
REMOTE_SETTING_URL=http://kinto:8888/v1/buckets/main/collections/nimbus-web-experiments/records
APP_ID=demo-app-beta
APP_NAME=demo_app
CHANNEL=beta
CIRRUS_FML_PATH=./feature_manifest/sample.yml
```
