/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import PageEditOverview from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import FormOverview from "../FormOverview";

const { mock, experiment } = mockExperimentQuery("demo-slug");

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

let mockMutationData: Record<string, string | boolean> = {};
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
    mockMutationData = {
      changelogMessage: CHANGELOG_MESSAGES.UPDATED_OVERVIEW,
      name: experiment.name,
      hypothesis: experiment.hypothesis!,
      publicDescription: experiment.publicDescription!,
      riskBrand: experiment.riskBrand!,
      riskRevenue: experiment.riskRevenue!,
      riskPartnerRelated: experiment.riskPartnerRelated!,
    };
    mockSubmitData = {
      ...mockMutationData,
      ...{
        riskBrand: String(experiment.riskBrand!),
        riskRevenue: String(experiment.riskRevenue!),
        riskPartnerRelated: String(experiment.riskPartnerRelated!),
      },
    };
    mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
      {
        ...mockMutationData,
        id: experiment.id,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_OVERVIEW,
      },
      "updateExperiment",
      {
        experiment: mockMutationData,
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

  it("handles form submission", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditOverview");
    fireEvent.click(screen.getByTestId("submit"));
    await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      name: { message: "already exists" },
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

  it("handles form next button", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditOverview");
    fireEvent.click(screen.getByTestId("next"));
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
      expect(navigate).toHaveBeenCalledWith("branches");
    });
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormOverview", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormOverview>) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSubmit(mockSubmitData, false);
    };
    const handleNext = (ev: React.FormEvent) => {
      ev.preventDefault();
      mockSubmit();
      props.onSubmit(mockSubmitData, true);
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
