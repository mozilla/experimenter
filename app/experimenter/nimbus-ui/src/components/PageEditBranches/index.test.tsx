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
import { navigate } from "@reach/router";
import PageEditBranches, { SUBMIT_ERROR_MESSAGE } from ".";
import FormBranches from "../FormBranches";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import { UPDATE_EXPERIMENT_BRANCHES_MUTATION } from "../../gql/experiments";
import {
  NimbusExperimentApplication,
  NimbusFeatureConfigApplication,
  UpdateExperimentBranchesInput,
} from "../../types/globalTypes";
import {
  updateExperimentBranches_updateExperimentBranches,
  updateExperimentBranches_updateExperimentBranches_nimbusExperiment,
} from "../../types/updateExperimentBranches";
import {
  FormBranchesSaveState,
  extractUpdateBranch,
} from "../FormBranches/reducer/update";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

describe("PageEditBranches", () => {
  beforeEach(() => {
    mockSetSubmitErrors.mockClear();
    mockClearSubmitErrors.mockClear();
  });

  afterEach(() => {});

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

    MOCK_CONFIG.featureConfig = [
      ...MOCK_CONFIG.featureConfig!,
      {
        __typename: "NimbusFeatureConfigType",
        id: "3",
        name: "Foo bar",
        slug: "foo-bar",
        description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        application: NimbusFeatureConfigApplication.FIREFOX_DESKTOP,
        ownerEmail: "dude23@yahoo.com",
        schema: '{ "sample": "schema" }',
      },
    ];

    // Assert that we have all the feature configs for our application (Fenix) available
    for (const feature of MOCK_CONFIG!.featureConfig!.filter(
      (config) => config?.application === experiment.application,
    )) {
      const { slug } = feature!;
      expect(screen.getByText(slug)).toBeInTheDocument();
    }

    // Assert that non of the feature configs that don't belong to our application are available
    for (const feature of MOCK_CONFIG!.featureConfig!.filter(
      (config) =>
        config?.application === NimbusFeatureConfigApplication.FIREFOX_DESKTOP,
    )) {
      const { slug } = feature!;
      expect(screen.queryByText(slug)).not.toBeInTheDocument();
    }
  });

  it("handles onNext from FormBranches", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("next-button"));
    expect(navigate).toHaveBeenCalledWith("metrics");
  });

  it("handles onSave from FormBranches", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);
    const mockMutation = mockUpdateExperimentBranchesMutation(
      { ...mockUpdateState, nimbusExperimentId: 1 },
      { experiment },
    );
    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });
    await act(async () => {
      const saveButton = await screen.getByTestId("save-button");
      await fireEvent.click(saveButton);
    });
    expect(mockSetSubmitErrors).not.toHaveBeenCalled();
  });

  it("sets a global submit error when updateExperimentBranches fails", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);

    const mockMutation = mockUpdateExperimentBranchesMutation(
      { ...mockUpdateState, nimbusExperimentId: 1 },
      { experiment },
    );
    // @ts-ignore - intentionally breaking this type for error handling
    delete mockMutation.result.data.updateExperimentBranches;

    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });

    await act(async () => {
      const saveButton = await screen.getByTestId("save-button");
      await fireEvent.click(saveButton);
    });

    expect(mockSetSubmitErrors).toHaveBeenCalledWith({
      "*": [SUBMIT_ERROR_MESSAGE],
    });
  });

  it("sets submit errors when updateExperimentBranches is not a success", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    setMockUpdateState(experiment);

    const mockMutation = mockUpdateExperimentBranchesMutation(
      { ...mockUpdateState, nimbusExperimentId: 1 },
      { experiment },
    );

    mockMutation.result.data.updateExperimentBranches.message = {
      reference_branch: {
        name: ["This name stinks."],
      },
    };

    render(<Subject mocks={[mock, mockMutation, mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });

    await act(async () => {
      const saveButton = await screen.getByTestId("save-button");
      await fireEvent.click(saveButton);
    });

    expect(mockSetSubmitErrors).toHaveBeenCalledWith(
      mockMutation.result.data.updateExperimentBranches.message,
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
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

const mockSetSubmitErrors = jest.fn();
const mockClearSubmitErrors = jest.fn();
let mockUpdateState: FormBranchesSaveState;

function setMockUpdateState(experiment: getExperiment_experimentBySlug) {
  // issue #3954: Need to parse string IDs into numbers
  const featureConfigId =
    experiment.featureConfig === null
      ? null
      : parseInt(experiment.featureConfig.id, 10);
  mockUpdateState = {
    featureConfigId,
    // @ts-ignore type mismatch covers discarded annotation properties
    referenceBranch: extractUpdateBranch(experiment.referenceBranch!),
    treatmentBranches: experiment.treatmentBranches!.map((branch) =>
      // @ts-ignore type mismatch covers discarded annotation properties
      extractUpdateBranch(branch!),
    ),
  };
}

jest.mock("../FormBranches", () => ({
  __esModule: true,
  default: ({
    experiment,
    featureConfig,
    onSave,
    onNext,
  }: React.ComponentProps<typeof FormBranches>) => {
    return (
      <div data-testid="FormBranches">
        {experiment && (
          <span data-testid="experiment-slug">{experiment.slug}</span>
        )}
        {featureConfig && (
          <ul data-testid="feature-config">
            {featureConfig.map(
              (feature, idx) =>
                feature && <li key={`feature-${idx}`}>{feature.slug}</li>,
            )}
          </ul>
        )}
        <button data-testid="next-button" onClick={() => onNext()}>
          Next
        </button>
        <button
          data-testid="save-button"
          type="submit"
          onClick={() =>
            onSave(mockUpdateState, mockSetSubmitErrors, mockClearSubmitErrors)
          }
        >
          <span>Save</span>
        </button>
      </div>
    );
  },
}));

export const mockUpdateExperimentBranchesMutation = (
  input: Partial<UpdateExperimentBranchesInput>,
  {
    clientMutationId = "8675309",
    status = 200,
    message = "success",
    experiment,
  }: {
    clientMutationId?: string | null;
    status?: number;
    message?: string | Record<string, any>;
    experiment: updateExperimentBranches_updateExperimentBranches_nimbusExperiment;
  },
) => {
  const updateExperimentBranches: updateExperimentBranches_updateExperimentBranches = {
    __typename: "UpdateExperimentBranches",
    clientMutationId,
    status,
    message,
    nimbusExperiment: experiment,
  };
  return {
    request: {
      query: UPDATE_EXPERIMENT_BRANCHES_MUTATION,
      variables: {
        input,
      },
    },
    result: {
      errors: undefined as undefined | any[],
      data: {
        updateExperimentBranches,
      },
    },
  };
};
