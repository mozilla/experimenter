/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  cleanup,
  act,
} from "@testing-library/react";
import { MockedCache } from "../../lib/mocks";
import PageNew from ".";
import { navigate } from "@reach/router";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";

jest.mock("@reach/router", () => ({
  navigate: jest.fn(),
}));

describe("PageNew", () => {
  beforeEach(() => {
    origConsoleLog = global.console.log;
    global.console.log = jest.fn();
    mockSubmit = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "firefox-desktop",
    };
  });

  afterEach(() => {
    global.console.log = origConsoleLog;
    cleanup();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () => {
      expect(screen.getByTestId("PageNew")).toBeInTheDocument();
    });
  });

  it("handles experiment form submission", async () => {
    const gqlMocks = mkGqlMocks();
    render(<Subject {...{ gqlMocks }} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(navigate).toHaveBeenCalledWith("foo-bar-baz/edit/overview");
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      name: { message: "already exists" },
    };
    const gqlMocks = mkGqlMocks({
      message: expectedErrors,
    });
    render(<Subject {...{ gqlMocks }} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify(expectedErrors),
    );
  });

  it("handles experiment form submission with bad server data", async () => {
    const gqlMocks = mkGqlMocks();
    // @ts-ignore - intentionally breaking this type for error handling
    delete gqlMocks[0].result.data.createExperiment;

    render(<Subject {...{ gqlMocks }} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify({ "*": SUBMIT_ERROR }),
    );
  });

  it("handles experiment form submission with server API error", async () => {
    const gqlMocks = mkGqlMocks();
    gqlMocks[0].result.errors = [new Error("an error")];

    render(<Subject {...{ gqlMocks }} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify({ "*": SUBMIT_ERROR }),
    );
  });

  it("handles experiment form cancellation", () => {
    render(<Subject />);
    fireEvent.click(screen.getByTestId("cancel"));
    expect(global.console.log).toHaveBeenCalledWith("CANCEL TBD");
  });

  const mkGqlMocks = ({
    message = "success" as string | Record<string, any>,
    status = 200,
    nimbusExperiment = { ...mockSubmit, slug: "foo-bar-baz" },
  } = {}) => [
    {
      request: {
        query: CREATE_EXPERIMENT_MUTATION,
        variables: {
          input: mockSubmit,
        },
      },
      result: {
        errors: undefined as undefined | any[],
        data: {
          createExperiment: {
            clientMutationId: "8675309",
            message,
            status,
            nimbusExperiment,
          },
        },
      },
    },
  ];

  const Subject = ({ gqlMocks = [] }: { gqlMocks?: any[] }) => {
    return (
      <MockedCache mocks={gqlMocks}>
        <PageNew />
      </MockedCache>
    );
  };
});

let origConsoleLog: typeof global.console.log;
let mockSubmit: Record<string, string> = {};

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormExperimentOverviewPartial", () => ({
  __esModule: true,
  default: (props: {
    isLoading: boolean;
    submitErrors?: Record<string, string[]>;
    onSubmit: Function;
    onCancel: (ev: React.FormEvent) => void;
    applications: string[];
  }) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onSubmit(mockSubmit, jest.fn());
    };
    const handleCancel = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onCancel(ev);
    };
    return (
      <div data-testid="FormExperimentOverviewPartial">
        <div data-testid="submitErrors">
          {JSON.stringify(props.submitErrors)}
        </div>
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="cancel" onClick={handleCancel} />
      </div>
    );
  },
}));
