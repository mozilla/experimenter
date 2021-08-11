import React from "react";
import { ApolloErrorAlert } from ".";
import {
  GQL_ERROR,
  GQL_ERROR_MULTIPLE,
  NETWORK_SERVER_ERROR,
  NETWORK_SERVER_PARSE_ERROR,
} from "./mocks";

export default {
  title: "components/ApolloErrorAlert",
  component: ApolloErrorAlert,
};

export const withError = () => (
  <ApolloErrorAlert
    error={new Error("Uh oh. You made the app crashy crash.")}
  />
);

export const withNetworkServerError = () => (
  <ApolloErrorAlert error={NETWORK_SERVER_ERROR} />
);

export const withNetworkServerParseError = () => (
  <ApolloErrorAlert error={NETWORK_SERVER_PARSE_ERROR} />
);

export const withGQLError = () => <ApolloErrorAlert error={GQL_ERROR} />;

export const withMultipleGQLErrors = () => (
  <ApolloErrorAlert error={GQL_ERROR_MULTIPLE} />
);
