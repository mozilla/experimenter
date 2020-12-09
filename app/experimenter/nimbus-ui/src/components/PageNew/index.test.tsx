/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { MockedCache, mockExperimentMutation } from "../../lib/mocks";
import PageNew from ".";
import { navigate } from "@reach/router";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { MockedResponse } from "@apollo/client/testing";

jest.mock("@reach/router", () => ({
  navigate: jest.fn(),
}));

describe("PageNew", () => {
  let mutationMock: any;

  beforeEach(() => {
    mockSubmit = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "firefox-desktop",
    };
    mutationMock = mockExperimentMutation(
      CREATE_EXPERIMENT_MUTATION,
      mockSubmit,
      "createExperiment",
      {
        experiment: { ...mockSubmit, slug: "foo-bar-baz" },
      },
    );
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () => {
      expect(screen.getByTestId("PageNew")).toBeInTheDocument();
    });
  });

  it("handles experiment form submission", async () => {
    render(<Subject mocks={[mutationMock]} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(navigate).toHaveBeenCalledWith("foo-bar-baz/edit/overview");
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      name: { message: "already exists" },
    };
    mutationMock.result.data.createExperiment.message = expectedErrors;
    render(<Subject mocks={[mutationMock]} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify(expectedErrors),
    );
  });

  it("handles experiment form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.createExperiment;
    render(<Subject mocks={[mutationMock]} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit"));
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify({ "*": SUBMIT_ERROR }),
    );
  });

  it("handles experiment form submission with server API error", async () => {
    mutationMock.result.errors = [new Error("an error")];
    render(<Subject mocks={[mutationMock]} />);
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
    expect(navigate).toHaveBeenCalledWith(".");
  });

  const Subject = ({
    mocks = [],
  }: {
    mocks?: MockedResponse<Record<string, any>>[];
  }) => {
    return (
      <MockedCache {...{ mocks }}>
        <PageNew />
      </MockedCache>
    );
  };
});

let mockSubmit: Record<string, string> = {};

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormOverview", () => ({
  __esModule: true,
  default: (props: {
    isLoading: boolean;
    submitErrors?: Record<string, string[]>;
    onSubmit: Function;
    onCancel: () => void;
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
      <div data-testid="FormOverview">
        <div data-testid="submitErrors">
          {JSON.stringify(props.submitErrors)}
        </div>
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="cancel" onClick={handleCancel} />
      </div>
    );
  },
}));
