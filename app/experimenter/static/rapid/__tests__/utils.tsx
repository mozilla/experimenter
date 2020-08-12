import { render, RenderResult } from "@testing-library/react";
import { createMemoryHistory, MemoryHistory } from "history";
import React from "react";
import { Route, Router, Switch } from "react-router-dom";

import ExperimentProvider from "experimenter-rapid/contexts/experiment/provider";
import { ExperimentData } from "experimenter-types/experiment";

type RenderWithRouterResult = RenderResult & { history: MemoryHistory };

export function renderWithRouter(
  ui: React.ReactElement,
  {
    route = "/",
    matchRoutePath = route,
    exact = false,
    history = createMemoryHistory({ initialEntries: [route] }),
  } = {},
): RenderWithRouterResult {
  const Wrapper = ({ children }) => (
    <Router history={history}>
      <Switch>
        <Route exact={exact} path={matchRoutePath}>
          {children}
        </Route>
      </Switch>
    </Router>
  );
  return {
    ...render(ui, { wrapper: Wrapper }),
    // adding `history` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    history,
  };
}

interface WrapInExperimentProviderOptions {
  initialState?: ExperimentData;
}

export function wrapInExperimentProvider(
  ui: React.ReactElement,
  { initialState } = {} as WrapInExperimentProviderOptions,
): React.ReactElement {
  return (
    <ExperimentProvider initialState={initialState}>{ui}</ExperimentProvider>
  );
}
