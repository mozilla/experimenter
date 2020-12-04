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
import PageEditMetrics from ".";
import FormMetrics from "../FormMetrics";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { UPDATE_EXPERIMENT_PROBESETS_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";

const { mock, experiment } = mockExperimentQuery("demo-slug");

jest.mock("@reach/router", () => ({
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

let mockSubmitData: Record<string, number | number[]> = {};
const mockSubmit = jest.fn();

describe("PageEditMetrics", () => {
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
      nimbusExperimentId: parseInt(experiment.id),
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
      "updateExperimentProbeSets",
      mockResponse,
    );
  });

  it("renders as expected", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditMetrics")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
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
    delete mutationMock.result.data.updateExperimentProbeSets;
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
    mutationMock.result.data.updateExperimentProbeSets.message = {
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
jest.mock("../FormMetrics", () => ({
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
