/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  screen,
  render,
  waitFor,
  fireEvent,
  act,
} from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import PageEditAudience from ".";
import FormAudience from "../FormAudience";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { UPDATE_EXPERIMENT_AUDIENCE_MUTATION } from "../../gql/experiments";
import { BASE_PATH, SUBMIT_ERROR } from "../../lib/constants";
import {
  updateExperimentAudience_updateExperimentAudience,
  updateExperimentAudience_updateExperimentAudience_nimbusExperiment,
} from "../../types/updateExperimentAudience";
import {
  NimbusExperimentChannel,
  NimbusExperimentFirefoxMinVersion,
  NimbusExperimentStatus,
  NimbusExperimentTargetingConfigSlug,
  UpdateExperimentAudienceInput,
} from "../../types/globalTypes";

const { mock, experiment } = mockExperimentQuery("demo-slug");

let mockSubmitData: Partial<UpdateExperimentAudienceInput>;
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
      { ...mockSubmitData, nimbusExperimentId: parseInt(experiment.id, 10) },
      {
        experiment: {
          ...MOCK_FORM_DATA,
          __typename: "NimbusExperimentType",
          id: experiment.id!,
          proposedEnrollment: parseFloat(MOCK_FORM_DATA.proposedEnrollment),
        },
      },
    );
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageEditAudience")).toBeInTheDocument();
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

  it("handles form next button", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageEditAudience")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("next"));
    expect(navigate).toHaveBeenCalledWith("../request-review");
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
      channel: { message: "this is garbage" },
    };
    mutationMock.result.data.updateExperimentAudience.message = expectedErrors;
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

  it("handles form submission with bad server data", async () => {
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperimentAudience;
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
});

const MOCK_FORM_DATA = {
  channel: NimbusExperimentChannel.DESKTOP_NIGHTLY,
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion.FIREFOX_80,
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug.US_ONLY,
  populationPercent: "40",
  totalEnrolledClients: 68000,
  proposedEnrollment: "1.0",
  proposedDuration: 28,
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
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

const mockSubmit = jest.fn();

jest.mock("../FormAudience", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof FormAudience>) => {
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

export const mockUpdateExperimentAudienceMutation = (
  input: Partial<UpdateExperimentAudienceInput>,
  {
    clientMutationId = "8675309",
    status = 200,
    message = "success",
    experiment,
  }: {
    clientMutationId?: string | null;
    status?: number;
    message?: string | Record<string, any>;
    experiment: updateExperimentAudience_updateExperimentAudience_nimbusExperiment;
  },
) => {
  const updateExperimentAudience: updateExperimentAudience_updateExperimentAudience = {
    __typename: "UpdateExperimentAudience",
    clientMutationId,
    status,
    message,
    nimbusExperiment: experiment,
  };

  return {
    request: {
      query: UPDATE_EXPERIMENT_AUDIENCE_MUTATION,
      variables: {
        input,
      },
    },
    result: {
      errors: undefined as undefined | any[],
      data: {
        updateExperimentAudience,
      },
    },
  };
};
