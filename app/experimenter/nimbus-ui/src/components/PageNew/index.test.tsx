/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import PageNew from ".";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { MockedCache, mockExperimentMutation } from "../../lib/mocks";

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
      changelogMessage: CHANGELOG_MESSAGES.CREATED_EXPERIMENT,
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
    await screen.findByTestId("PageNew");
  });

  it("handles experiment form submission", async () => {
    render(<Subject mocks={[mutationMock]} />);
    fireEvent.click(screen.getByTestId("submit"));
    await waitFor(() =>
      expect(navigate).toHaveBeenCalledWith("foo-bar-baz/edit/overview"),
    );
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      name: { message: "already exists" },
    };
    mutationMock.result.data.createExperiment.message = expectedErrors;
    render(<Subject mocks={[mutationMock]} />);
    const submitButton = await screen.findByTestId("submit");
    fireEvent.click(submitButton);
    await waitFor(() =>
      expect(screen.getByTestId("submitErrors")).toHaveTextContent(
        JSON.stringify(expectedErrors),
      ),
    );
  });

  it("handles experiment form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.createExperiment;
    render(<Subject mocks={[mutationMock]} />);
    const submitButton = await screen.findByTestId("submit");
    fireEvent.click(submitButton);
    await waitFor(() =>
      expect(screen.getByTestId("submitErrors")).toHaveTextContent(
        JSON.stringify({ "*": SUBMIT_ERROR }),
      ),
    );
  });

  it("handles experiment form submission with server API error", async () => {
    mutationMock.result.errors = [new Error("an error")];
    render(<Subject mocks={[mutationMock]} />);
    fireEvent.click(screen.getByTestId("submit"));
    await waitFor(() =>
      expect(screen.getByTestId("submitErrors")).toHaveTextContent(
        JSON.stringify({ "*": SUBMIT_ERROR }),
      ),
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
    onSubmit: (data: Record<string, string>, mock: jest.Mock<any, any>) => void;
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
