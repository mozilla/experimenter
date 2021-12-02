/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import {
  createHistory,
  createMemorySource,
  History,
  HistorySource,
  LocationProvider,
  RouteComponentProps,
  Router,
  useLocation,
} from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
import { SearchParamsStateProvider } from "../hooks";
import { snakeToCamelCase } from "./caseConversions";
import { MockedCache, mockExperimentQuery } from "./mocks";

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
  path = "/demo-slug/edit",
  mocks = [],
  children,
  mockHistorySource,
  mockHistory,
}: {
  path?: string;
  mocks?: MockedResponse<Record<string, any>>[];
  mockHistorySource?: HistorySource;
  mockHistory?: History;
  children: React.ReactElement;
}) => {
  const source = mockHistorySource || createMemorySource(path);
  const history = mockHistory || createHistory(source);

  return (
    <SearchParamsStateProvider>
      <LocationProvider {...{ history }}>
        <Router>
          <Route
            path=":slug/edit"
            data-testid="app"
            component={() => (
              <MockedCache {...{ mocks }}>{children}</MockedCache>
            )}
          />
        </Router>
      </LocationProvider>
    </SearchParamsStateProvider>
  );
};

const Route = (
  props: { component: () => React.ReactNode } & RouteComponentProps,
) => <div {...{ props }}>{props.component()}</div>;

const assertFieldErrors = async (errors: string[], selector: string) => {
  await screen.findByText(errors.join(", "), {
    selector: `[data-for="${snakeToCamelCase(selector)}"]`,
  });
};

export const assertSerializerMessages = async (
  Subject: React.ComponentType<any>,
  messages: SerializerMessages,
) => {
  Object.defineProperty(window, "location", {
    value: {
      search: "?show-errors",
    },
  });

  const { experiment } = mockExperimentQuery("boo", {
    featureConfigs: [],
    readyForReview: {
      ready: false,
      message: messages,
    },
  });

  render(<Subject {...{ experiment }} />);

  for (const [field, errors] of Object.entries(messages)) {
    // An object of serializer messages contains values of either:
    // - an array of strings
    // - an object containing this same thing
    // - an array of objects containing this same thing

    // Skip `feature_config` because it's displayed on the branches page and accounted
    // for in branch-specific tests
    if (field !== "feature_config") {
      // First we'll see if the errors are an array
      if (Array.isArray(errors)) {
        // Then check if the errors are objects, indicating nested fields
        if (typeof errors[0] === "object") {
          let index = 0;
          for (const set of errors) {
            for (const [innerField, innerErrors] of Object.entries(set)) {
              await assertFieldErrors(
                innerErrors,
                `${field}[${index}].${innerField}`,
              );
            }
            index++;
          }
          // Otherwise we know the array is strings for the top-level field
        } else {
          await assertFieldErrors(errors as string[], snakeToCamelCase(field));
        }
        // If the errors aren't an array we know there are child fields
      } else {
        for (const [innerField, innerErrors] of Object.entries(errors)) {
          await assertFieldErrors(innerErrors, `${field}.${innerField}`);
        }
      }
    }
  }
};

export const CurrentLocation = () => {
  const location = useLocation();
  return (
    <p className="p-3">
      Location:{" "}
      <code data-testid="location">
        {location.pathname}
        {location.search}
      </code>
    </p>
  );
};
