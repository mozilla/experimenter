/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Alert } from "react-bootstrap";
import sentryMetrics from "../../services/sentry";

class AppErrorBoundary extends React.Component {
  state: {
    error: undefined | Error;
  };

  constructor(props: Record<string, any>) {
    super(props);
    this.state = { error: undefined };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    sentryMetrics.captureException(error);
  }

  render() {
    const { error } = this.state;
    return error ? <AppErrorAlert {...{ error }} /> : this.props.children;
  }
}

export const AppErrorAlert = ({ error }: { error: Error }) => (
  <Alert variant="danger" data-testid="error-loading-app">
    <Alert.Heading>General application error</Alert.Heading>
    <p>Something went wrong. Please try again later.</p>
    {error?.message && (
      <>
        <hr />
        <small>{"" + error.message}</small>
      </>
    )}
  </Alert>
);

export default AppErrorBoundary;
