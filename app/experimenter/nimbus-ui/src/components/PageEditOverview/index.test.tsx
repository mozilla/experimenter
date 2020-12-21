/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  screen,
  waitFor,
  render,
  fireEvent,
  act,
} from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import PageEditOverview from ".";
import FormOverview from "../FormOverview";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { UPDATE_EXPERIMENT_OVERVIEW_MUTATION } from "../../gql/experiments";
import { BASE_PATH, SUBMIT_ERROR } from "../../lib/constants";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { mock, experiment } = mockExperimentQuery("demo-slug");

jest.mock("@reach/router", () => ({
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

let mockSubmitData: Record<string, string> = {};
const mockSubmit = jest.fn();

describe("PageEditOverview", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  let mutationMock: any;

  const Subject = ({
    mocks = [],
  }: {
    mocks?: MockedResponse<Record<string, any>>[];
  }) => {
    return (
      <RouterSlugProvider {...{ mocks }}>
        <PageEditOverview />
      </RouterSlugProvider>
    );
  };

  beforeEach(() => {
    mockSubmitData = {
      name: experiment.name,
      hypothesis: experiment.hypothesis!,
      publicDescription: experiment.publicDescription!,
    };
    mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_OVERVIEW_MUTATION,
      { ...mockSubmitData, id: experiment.id },
      "updateExperimentOverview",
      {
        experiment: mockSubmitData,
      },
    );
  });

  it("renders as expected", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
  });

  it("redirects to the review page if the experiment status is review", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/request-review`,
        {
          replace: true,
        },
      );
    });
  });

  it("redirects to the design page if the experiment status is live", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/design`,
        {
          replace: true,
        },
      );
    });
  });

  it("redirects to the design page if the experiment status is complete", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/design`,
        {
          replace: true,
        },
      );
    });
  });

  it("handles form submission", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);

    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      submitButton = screen.getByTestId("submit") as HTMLButtonElement;
    });
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(mockSubmit).toHaveBeenCalled();
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      name: { message: "already exists" },
    };
    mutationMock.result.data.updateExperimentOverview.message = expectedErrors;
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      submitButton = screen.getByTestId("submit") as HTMLButtonElement;
    });
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify(expectedErrors),
    );
  });

  it("handles experiment form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperimentOverview;
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      submitButton = screen.getByTestId("submit") as HTMLButtonElement;
    });
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify({ "*": SUBMIT_ERROR }),
    );
  });

  it("handles experiment form submission with server API error", async () => {
    mutationMock.result.errors = [new Error("an error")];
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      submitButton = screen.getByTestId("submit") as HTMLButtonElement;
    });
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(screen.getByTestId("submitErrors")).toHaveTextContent(
      JSON.stringify({ "*": SUBMIT_ERROR }),
    );
  });

  it("handles form next button", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => fireEvent.click(screen.getByTestId("next")));
    expect(navigate).toHaveBeenCalledWith("branches");
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormOverview", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormOverview>) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSubmit(mockSubmitData, jest.fn());
    };
    const handleNext = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onNext && props.onNext(ev);
    };
    return (
      <div data-testid="FormOverview">
        <div data-testid="submitErrors">
          {JSON.stringify(props.submitErrors)}
        </div>
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="next" onClick={handleNext} />
      </div>
    );
  },
}));
