/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import {
  createHistory,
  createMemorySource,
  LocationProvider,
  RouteComponentProps,
  Router,
} from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
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
}: {
  path?: string;
  mocks?: MockedResponse<Record<string, any>>[];
  children: React.ReactElement;
}) => {
  const source = createMemorySource(path);
  const history = createHistory(source);

  return (
    <LocationProvider {...{ history }}>
      <Router>
        <Route
          path=":slug/edit"
          data-testid="app"
          component={() => <MockedCache {...{ mocks }}>{children}</MockedCache>}
        />
      </Router>
    </LocationProvider>
  );
};

const Route = (
  props: { component: () => React.ReactNode } & RouteComponentProps,
) => <div {...{ props }}>{props.component()}</div>;

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
    readyForReview: {
      ready: false,
      message: messages,
    },
  });

  render(<Subject {...{ experiment }} />);

  for (const [field, errors] of Object.entries(messages)) {
    // An object of serializer messages contains values of either:
    // - an array of strings
    // - an array of objects containing this same thing, indicating nested fields
    // We start by checking if the field contains nested fields
    if (typeof errors[0] === "object") {
      let index = 0;
      for (const set of errors) {
        for (const [innerField, innerErrors] of Object.entries(set)) {
          await screen.findByText(innerErrors.join(", "), {
            selector: `[data-for="${snakeToCamelCase(
              field,
            )}[${index}].${snakeToCamelCase(innerField)}"]`,
          });
        }
        index++;
      }
    } else {
      await screen.findByText(errors.join(", "), {
        selector: `[data-for="${snakeToCamelCase(field)}"]`,
      });
    }
  }
};
