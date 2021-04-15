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
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import {
  createFullStatusMutationMock,
  createPublishStatusMutationMock,
  createStatusMutationMock,
  reviewRequestedBaseProps,
  Subject,
} from "./mocks";

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

describe("PageRequestReview", () => {
  const origError = global.console.error;
  const origWindowOpen = global.window.open;

  let mockError: any;
  let mockWindowOpen: any;

  beforeAll(() => {
    fetchMock.enableMocks();
  });

  beforeEach(() => {
    mockError = jest.fn();
    mockWindowOpen = jest.fn();
    global.console.error = mockError;
    global.window.open = mockWindowOpen;
  });

  afterEach(() => {
    global.console.error = origError;
    global.window.open = origWindowOpen;
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

  it("redirects to the summary page if the experiment status is live", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(`${BASE_PATH}/${experiment.slug}`, {
        replace: true,
      });
    });
  });

  it("redirects to the summary page if the experiment status is complete", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(`${BASE_PATH}/${experiment.slug}`, {
        replace: true,
      });
    });
  });

  it("indicates status in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("indicates status in preview", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("in-preview-label");
  });

  it("handles Launch to Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
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
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentPublishStatus.REVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
  });

  it("handles cancelled Launch to Review as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    render(<Subject mocks={[mock, mutationMock]} />);

    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;

    await act(async () => void fireEvent.click(startButton));

    const cancelButton = await screen.findByTestId("cancel");
    await act(async () => void fireEvent.click(cancelButton));
    await screen.findByTestId("launch-draft-to-preview");
  });

  it("handles Launch to Preview after reconsidering Launch to Review from Draft", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
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
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-preview-to-draft",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles approval of launch as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentPublishStatus.APPROVED,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const approveButton = await screen.findByTestId("approve-request");
    fireEvent.click(approveButton);
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    fireEvent.click(openRemoteSettingsButton);
    await waitFor(() => {
      expect(mockWindowOpen).toHaveBeenCalledWith(
        MOCK_CONFIG.kintoAdminUrl,
        "_blank",
      );
    });
  });

  it("handles rejection of launch as expected", async () => {
    const expectedReason = "This smells bad.";
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentPublishStatus.IDLE,
      expectedReason,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const rejectButton = await screen.findByTestId("reject-request");
    fireEvent.click(rejectButton);
    const rejectSubmitButton = await screen.findByTestId("reject-submit");
    const rejectReasonField = await screen.findByTestId("reject-reason");
    fireEvent.change(rejectReasonField, {
      target: { value: expectedReason },
    });
    fireEvent.blur(rejectReasonField);
    fireEvent.click(rejectSubmitButton);
  });

  it("handles submission with server API error", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
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
    const mutationMock = createPublishStatusMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatus.REVIEW,
    );
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
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });
});
