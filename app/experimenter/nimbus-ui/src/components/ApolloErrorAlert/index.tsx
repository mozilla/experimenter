/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloError, ServerError, ServerParseError } from "@apollo/client";
import { GraphQLError } from "graphql";
import React from "react";
import { Alert } from "react-bootstrap";
import sentryMetrics from "../../services/sentry";

export type NetworkError = ApolloError["networkError"];

// Type guards - If the `networkError` is a `ServerError`, we want to display its `result.errors`
// array containing extra info
function isNetworkServerError(
  networkError: NetworkError,
): networkError is ServerError {
  return (networkError as ServerError)?.result !== undefined;
}

// If the `networkError` is a `ServerParseError`, we want to display `bodyText` and `statusCode`
function isNetworkServerParseError(
  networkError: NetworkError,
): networkError is ServerParseError {
  return (
    (networkError as ServerParseError)?.bodyText !== undefined &&
    (networkError as ServerParseError)?.statusCode !== undefined
  );
}

export const ApolloErrorAlert = ({ error }: { error: ApolloError | Error }) => {
  const { graphQLErrors = [], networkError } = error as ApolloError;
  const networkServerErrors =
    networkError && isNetworkServerError(networkError)
      ? networkError.result.errors
      : [];

  // Report Errors and NetworkErrors, graphQLErrors should be captured server-side
  if (networkError || error instanceof Error) {
    sentryMetrics.captureException(error);
  }

  let heading = "General GQL Error";
  if (graphQLErrors.length) {
    heading = "GraphQL Apollo Error";
  } else if (networkError) {
    heading = "Network Error";
  }

  return (
    <Alert variant="danger" data-testid="apollo-error-alert">
      <Alert.Heading>{heading}</Alert.Heading>
      <p className="mb-6">Something went wrong. Please try again later.</p>
      <hr />
      {error.message && (
        <p>
          <b>Message:</b> {error.message}
        </p>
      )}
      {graphQLErrors.length > 0 &&
        graphQLErrors.map((gqlError: GraphQLError) => (
          <p key={gqlError.message}>
            <b>graphQL error:</b> {gqlError.message}
          </p>
        ))}
      {networkServerErrors.length > 0 &&
        networkServerErrors.map((serverError: ServerError) => (
          <p key={serverError.message}>
            <b>Network error:</b> {serverError.message}
          </p>
        ))}
      {networkError && isNetworkServerParseError(networkError) && (
        <>
          <p>
            <b>Status code:</b> {networkError.statusCode}
          </p>
          <p>
            <b>Body text:</b> {networkError.bodyText}
          </p>
        </>
      )}
    </Alert>
  );
};

export default ApolloErrorAlert;
