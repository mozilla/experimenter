/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import PageEditMetrics from ".";
import { UPDATE_EXPERIMENT_PROBESETS_MUTATION } from "../../gql/experiments";
import { BASE_PATH, EXTERNAL_URLS, SUBMIT_ERROR } from "../../lib/constants";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import FormMetrics from "./FormMetrics";

const { mock, experiment } = mockExperimentQuery("demo-slug");

jest.mock("@reach/router", () => ({
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

let mockSubmitData: Record<string, number | number[]> = {};
const mockSubmit = jest.fn();

describe("PageEditMetrics", () => {
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
        <PageEditMetrics />
      </RouterSlugProvider>
    );
  };

  beforeEach(() => {
    mockSubmitData = {
      id: experiment.id!,
      primaryProbeSetIds: experiment.primaryProbeSets!.map((p) =>
        parseInt(p!.id),
      ),
      secondaryProbeSetIds: experiment.secondaryProbeSets!.map((p) =>
        parseInt(p!.id),
      ),
    };
    const mockResponse = {
      experiment: {
        id: experiment.id,
        primaryProbeSets: experiment.primaryProbeSets!.map((p) => ({
          id: p?.id,
          name: p?.name,
        })),
        secondaryProbeSets: experiment.secondaryProbeSets!.map((p) => ({
          id: p?.id,
          name: p?.name,
        })),
      },
    };

    mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_PROBESETS_MUTATION,
      mockSubmitData,
      "updateExperiment",
      mockResponse,
    );
  });

  it("renders as expected", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditMetrics")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
      expect(screen.getByTestId("core-metrics-link")).toHaveAttribute(
        "href",
        EXTERNAL_URLS.METRICS_GOOGLE_DOC,
      );
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

  it("redirects to the review page if the experiment status is preview", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      // @ts-ignore EXP-879 mock value until backend API & types are updated
      status: NimbusExperimentStatus.PREVIEW,
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

  it("handles experiment form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperiment;
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

  it("handles server validation error", async () => {
    mutationMock.result.data.updateExperiment.message = {
      primaryProbeSets: ["Bad probe sets"],
    };
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      submitButton = screen.getByTestId("submit") as HTMLButtonElement;
    });
    await act(async () => {
      fireEvent.click(submitButton);
    });
  });

  it("handles form next button", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => fireEvent.click(screen.getByTestId("next")));
    expect(navigate).toHaveBeenCalledWith("audience");
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("./FormMetrics", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormMetrics>) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSave(mockSubmitData, jest.fn());
    };
    const handleNext = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onNext && props.onNext(ev);
    };
    return (
      <div data-testid="FormMetrics">
        <div data-testid="submitErrors">
          {JSON.stringify(props.submitErrors)}
        </div>
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="next" onClick={handleNext} />
      </div>
    );
  },
}));
