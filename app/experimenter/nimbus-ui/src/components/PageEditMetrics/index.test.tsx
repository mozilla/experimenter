/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import PageEditMetrics from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SUBMIT_ERROR,
} from "../../lib/constants";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { OutcomeSlugs } from "../../lib/types";
import FormMetrics from "./FormMetrics";

const { mock, experiment } = mockExperimentQuery("demo-slug");

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

let mockSubmitData: { [key: string]: OutcomeSlugs | number | string } = {};
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
      changelogMessage: CHANGELOG_MESSAGES.UPDATED_OUTCOMES,
      primaryOutcomes: experiment.primaryOutcomes!,
      secondaryOutcomes: experiment.secondaryOutcomes!,
    };
    const mockResponse = {
      experiment: {
        id: experiment.id,
        primaryOutcomes: experiment.primaryOutcomes!,
        secondaryOutcomes: experiment.secondaryOutcomes!,
      },
    };

    mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
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

  it("handles form submission", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditMetrics");
    fireEvent.click(screen.getByTestId("submit"));
    await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
  });

  it("handles experiment form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperiment;
    render(<Subject mocks={[mock, mutationMock]} />);
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
    render(<Subject mocks={[mock, mutationMock]} />);
    const submitButton = await screen.findByTestId("submit");
    fireEvent.click(submitButton);
    await waitFor(() =>
      expect(screen.getByTestId("submitErrors")).toHaveTextContent(
        JSON.stringify({ "*": SUBMIT_ERROR }),
      ),
    );
  });

  it("handles server validation error", async () => {
    const expectedErrors = {
      primaryOutcomes: ["Bad outcomes"],
    };
    mutationMock.result.data.updateExperiment.message = expectedErrors;
    render(<Subject mocks={[mock, mutationMock]} />);
    const submitButton = await screen.findByTestId("submit");
    fireEvent.click(submitButton);
    await waitFor(() =>
      expect(screen.getByTestId("submitErrors")).toHaveTextContent(
        JSON.stringify(expectedErrors),
      ),
    );
  });

  it("handles form next button", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditMetrics");
    fireEvent.click(screen.getByTestId("next"));
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
      expect(navigate).toHaveBeenCalledWith("audience");
    });
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("./FormMetrics", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormMetrics>) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSave(mockSubmitData, false);
    };
    const handleNext = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSave(mockSubmitData, true);
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
