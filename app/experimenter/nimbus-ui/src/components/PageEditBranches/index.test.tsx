/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import PageEditBranches from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SUBMIT_ERROR,
} from "../../lib/constants";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentApplication,
} from "../../types/globalTypes";
import { updateExperiment_updateExperiment } from "../../types/updateExperiment";
import FormBranches from "./FormBranches";
import { FormBranchesSaveState } from "./FormBranches/reducer";
import { extractUpdateBranch } from "./FormBranches/reducer/update";

describe("PageEditBranches", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  beforeEach(() => {
    mockSetSubmitErrors.mockClear();
    mockClearSubmitErrors.mockClear();
  });

  it("renders as expected with experiment data", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplication.FENIX,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("feature-config")).toBeInTheDocument();
    expect(screen.getByTestId("learn-more-link")).toHaveAttribute(
      "href",
      EXTERNAL_URLS.BRANCHES_GOOGLE_DOC,
    );

    for (const feature of MOCK_CONFIG!.featureConfigs!) {
      const { name, application } = feature!;
      const configEl = screen.queryByText(name);
      if (application === experiment!.application) {
        expect(configEl).toBeInTheDocument();
      } else {
        expect(configEl).not.toBeInTheDocument();
      }
    }
  });

  it("handles onSave with next from FormBranches", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);
    const mockMutation = mockUpdateExperimentBranchesMutation(
      {
        ...mockUpdateState,
        id: 1,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
      },
      {},
    );
    render(<Subject mocks={[mock, mockMutation]} />);
    await screen.findByTestId("PageEditBranches");
    fireEvent.click(screen.getByTestId("next-button"));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith("metrics"));
  });

  it("handles onSave from FormBranches", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);
    const mockMutation = mockUpdateExperimentBranchesMutation(
      {
        ...mockUpdateState,
        id: 1,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
      },
      {},
    );
    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await screen.findByTestId("PageEditBranches");
    fireEvent.click(screen.getByTestId("save-button"));
    await waitFor(() => expect(mockSetSubmitErrors).not.toHaveBeenCalled());
  });

  it("sets a global submit error when updateExperimentBranches fails", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);

    const mockMutation = mockUpdateExperimentBranchesMutation(
      {
        ...mockUpdateState,
        id: 1,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
      },
      {},
    );
    // @ts-ignore - intentionally breaking this type for error handling
    delete mockMutation.result.data.updateExperiment;

    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await screen.findByTestId("PageEditBranches");

    const saveButton = screen.getByTestId("save-button");
    fireEvent.click(saveButton);

    await waitFor(() =>
      expect(mockSetSubmitErrors).toHaveBeenCalledWith({
        "*": [SUBMIT_ERROR],
      }),
    );
  });

  it("sets submit errors when updateExperimentBranches is not a success", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);

    const mockMutation = mockUpdateExperimentBranchesMutation(
      {
        ...mockUpdateState,
        id: 1,
        changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
      },
      {},
    );

    mockMutation.result.data.updateExperiment.message = {
      reference_branch: {
        name: ["This name stinks."],
      },
    };

    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await screen.findByTestId("PageEditBranches");

    const saveButton = screen.getByTestId("save-button");
    fireEvent.click(saveButton);

    await waitFor(() =>
      expect(mockSetSubmitErrors).toHaveBeenCalledWith(
        mockMutation.result.data.updateExperiment.message,
      ),
    );
  });
});

const Subject = ({
  mocks = [],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageEditBranches />
  </RouterSlugProvider>
);

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

const mockSetSubmitErrors = jest.fn();
const mockClearSubmitErrors = jest.fn();
let mockUpdateState: FormBranchesSaveState;

function setMockUpdateState(experiment: getExperiment_experimentBySlug) {
  const featureConfigId =
    experiment.featureConfig === null ? null : experiment.featureConfig.id;
  mockUpdateState = {
    featureConfigId,
    // @ts-ignore type mismatch covers discarded annotation properties
    referenceBranch: extractUpdateBranch(experiment.referenceBranch!),
    treatmentBranches: experiment.treatmentBranches!.map(
      (branch) =>
        // @ts-ignore type mismatch covers discarded annotation properties
        extractUpdateBranch(branch!)!,
    ),
  };
}

jest.mock("./FormBranches", () => ({
  __esModule: true,
  default: ({
    experiment,
    featureConfigs,
    onSave,
  }: React.ComponentProps<typeof FormBranches>) => {
    return (
      <div data-testid="FormBranches">
        {experiment && (
          <span data-testid="experiment-slug">{experiment.slug}</span>
        )}
        {featureConfigs && (
          <ul data-testid="feature-config">
            {featureConfigs.map(
              (feature, idx) =>
                feature && <li key={`feature-${idx}`}>{feature.name}</li>,
            )}
          </ul>
        )}
        <button
          data-testid="next-button"
          onClick={() =>
            onSave(
              mockUpdateState,
              mockSetSubmitErrors,
              mockClearSubmitErrors,
              true,
            )
          }
        >
          Save and Continue
        </button>
        <button
          data-testid="save-button"
          type="submit"
          onClick={() =>
            onSave(
              mockUpdateState,
              mockSetSubmitErrors,
              mockClearSubmitErrors,
              false,
            )
          }
        >
          <span>Save</span>
        </button>
      </div>
    );
  },
}));

export const mockUpdateExperimentBranchesMutation = (
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
