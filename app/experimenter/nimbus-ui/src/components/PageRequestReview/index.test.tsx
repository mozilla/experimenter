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
import {
  BASE_PATH,
  CHANGELOG_MESSAGES,
  SERVER_ERRORS,
} from "../../lib/constants";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import {
  createFullStatusMutationMock,
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

  it("displays a banner for pages missing fields required for review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: false,
        message: {
          channel: [SERVER_ERRORS.EMPTY_LIST],
        },
      },
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByText(/all required fields must be completed/);
    expect(screen.queryByTestId("launch-draft-to-preview")).toBeNull();
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
      CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
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
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.REVIEW,
      CHANGELOG_MESSAGES.REQUESTED_REVIEW,
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
      CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
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
      CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
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
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.APPROVED,
      CHANGELOG_MESSAGES.REVIEW_APPROVED,
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
      null,
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
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.REVIEW,
      CHANGELOG_MESSAGES.REQUESTED_REVIEW,
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

  it("shows no recommended signoff", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      signoffRecommendations: {
        qaSignoff: false,
        vpSignoff: false,
        legalSignoff: false,
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff")).not.toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows qa recommended signoff", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      signoffRecommendations: {
        qaSignoff: true,
        vpSignoff: false,
        legalSignoff: false,
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-qa")).toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows vp recommended signoff", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      signoffRecommendations: {
        qaSignoff: false,
        vpSignoff: true,
        legalSignoff: false,
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-vp")).toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows legal recommended signoff", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      signoffRecommendations: {
        qaSignoff: false,
        vpSignoff: false,
        legalSignoff: true,
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-legal")).toHaveTextContent(
        "Recommended",
      ),
    );
  });
});
