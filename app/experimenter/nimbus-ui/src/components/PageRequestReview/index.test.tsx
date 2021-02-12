/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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
import { BASE_PATH } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { createMutationMock, Subject } from "./mocks";

jest.mock("@reach/router", () => ({
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

describe("PageRequestReview", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  async function checkRequiredBoxes() {
    const checkboxes = screen.queryAllByTestId("required-checkbox");

    for (const checkbox of checkboxes) {
      await act(async () => void fireEvent.click(checkbox));
    }
  }

  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageRequestReview");
    await screen.findByTestId("start-launch-draft-to-review");
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
  });

  it("redirects to the first edit page containing missing fields if the experiment status is draft and its not ready for review", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
      readyForReview: {
        __typename: "NimbusReadyForReviewType",
        ready: false,
        message: {
          // This field exists on the Audience page
          firefox_min_version: ["This field may not be null."],
        },
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        navigate,
      ).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/edit/audience?show-errors`,
        { replace: true },
      );
    });
  });

  it("redirects to the overview edit page if the experiment status is draft and its not ready for review, and for some reason invalid pages is empty", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
      readyForReview: {
        __typename: "NimbusReadyForReviewType",
        ready: false,
        message: {},
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        navigate,
      ).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/edit/overview?show-errors`,
        { replace: true },
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

  it("indicates status in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("handles Launch to Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentStatus.PREVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-draft-to-preview",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles Launch without Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id!);
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
  });

  it("handles Launch to Preview after reconsidering Launch to Review from Draft", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentStatus.PREVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);

    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(startButton));

    const launchButton = (await screen.findByTestId(
      "launch-to-preview-instead",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles Back to Draft from Preview", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-preview-to-draft",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles submission with bad server data", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id!);
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperiment;
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toBeInTheDocument(),
    );
  });

  it("handles submission with server API error", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id!);
    mutationMock.result.errors = [new Error("Boo")];
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toBeInTheDocument(),
    );
  });

  it("handles submission with server-side validation errors", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id!);
    const errorMessage = "Something went very wrong.";
    mutationMock.result.data.updateExperiment.message = {
      status: [errorMessage],
    };
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() => {
      expect(screen.getByTestId("submit-error")).toBeInTheDocument();
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        errorMessage,
      );
    });
  });

  async function launchFromDraftToReview() {
    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;

    await act(async () => void fireEvent.click(startButton));

    const submitButton = await screen.findByTestId("launch-draft-to-review");

    expect(submitButton!).toBeDisabled();
    await checkRequiredBoxes();
    expect(submitButton!).toBeEnabled();

    await act(async () => void fireEvent.click(submitButton));
  }

  it("will not allow submitting if already in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });
});
