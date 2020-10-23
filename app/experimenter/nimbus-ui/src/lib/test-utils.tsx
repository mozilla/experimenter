/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  createHistory,
  createMemorySource,
  LocationProvider,
  RouteComponentProps,
  Router,
} from "@reach/router";
import { render } from "@testing-library/react";

export function renderWithRouter(
  ui: React.ReactElement,
  { route = "/", history = createHistory(createMemorySource(route)) } = {},
) {
  return {
    ...render(<LocationProvider {...{ history }}>{ui}</LocationProvider>),
    history,
  };
}

export const RouterSlugProvider = ({
  path = "/demoslug/edit",
  children,
}: {
  path?: string;
  children: React.ReactElement;
}) => {
  let source = createMemorySource(path);
  let history = createHistory(source);
  return (
    <LocationProvider {...{ history }}>
      <Router>
        <Route path=":slug/edit" data-testid="app" component={() => children} />
      </Router>
    </LocationProvider>
  );
};

const Route = (
  props: { component: () => React.ReactNode } & RouteComponentProps,
) => <div {...{ props }}>{props.component()}</div>;
