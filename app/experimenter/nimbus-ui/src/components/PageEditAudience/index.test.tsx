/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import PageEditAudience from "src/components/PageEditAudience";
import FormAudience from "src/components/PageEditAudience/FormAudience";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "src/lib/constants";
import { mockExperimentQuery } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import {
  ExperimentInput,
  NimbusExperimentChannelEnum,
  NimbusExperimentFirefoxVersionEnum,
} from "src/types/globalTypes";
import { updateExperiment_updateExperiment } from "src/types/updateExperiment";

const { mock, experiment } = mockExperimentQuery("demo-slug");

let mockSubmitData: Partial<ExperimentInput>;
let mutationMock: ReturnType<typeof mockUpdateExperimentAudienceMutation>;

describe("PageEditAudience", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  beforeEach(() => {
    mockSubmitData = { ...MOCK_FORM_DATA };
    mutationMock = mockUpdateExperimentAudienceMutation(
      {
        ...mockSubmitData,
        id: experiment.id,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_AUDIENCE,
      },
      {},
    );
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await screen.findByTestId("PageEditAudience");
  });

  it("handles form next button", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditAudience");
    fireEvent.click(screen.getByTestId("next"));
    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
      expect(navigate).toHaveBeenCalledWith("../");
    });
  });

  it("handles form submission", async () => {
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("PageEditAudience");
    fireEvent.click(screen.getByTestId("submit"));
    await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
  });

  it("handles experiment form submission with server-side validation errors", async () => {
    const expectedErrors = {
      channel: { message: "this is garbage" },
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

  it("handles form submission with bad server data", async () => {
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
});

const MOCK_FORM_DATA = {
  channel: NimbusExperimentChannelEnum.NIGHTLY,
  firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_83,
  firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_95,
  targetingConfigSlug: "FIRST_RUN",
  populationPercent: "40",
  totalEnrolledClients: 68000,
  proposedEnrollment: "7",
  proposedDuration: "28",
  countries: ["1"],
  locales: ["1"],
  languages: ["1"],
  isSticky: true,
  isFirstRun: true,
};

const Subject = ({
  mocks = [mock],
}: {
  mocks?: MockedResponse<Record<string, any>>[];
}) => {
  return (
    <RouterSlugProvider {...{ mocks }}>
      <PageEditAudience />
    </RouterSlugProvider>
  );
};

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

const mockSubmit = jest.fn();

jest.mock("./FormAudience", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormAudience>) => {
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

export const mockUpdateExperimentAudienceMutation = (
  input: Partial<ExperimentInput>,
  {
    message = "success",
  }: {
    message?: string | Record<string, any>;
  },
) => {
  const updateExperiment: updateExperiment_updateExperiment = {
    message,
  };

  return {
    request: {
      query: UPDATE_EXPERIMENT_MUTATION,
      variables: {
        input,
      },
    },
    result: {
      errors: undefined as undefined | any[],
      data: {
        updateExperiment,
      },
    },
  };
};
