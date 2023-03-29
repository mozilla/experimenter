/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import { createMutationMock, Subject } from "src/components/Summary/mocks";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "src/lib/constants";
import { mockExperimentQuery, mockLiveRolloutQuery } from "src/lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

describe("Summary", () => {
  it("renders expected components", () => {
    render(<Subject />);

    expect(screen.queryByTestId("experiment-end")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("link-monitoring-dashboard"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("table-overview")).toBeInTheDocument();
    expect(screen.getByTestId("table-risk-mitigation")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches",
    );
  });

  it("renders signoff table if experiment has been launched", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
        }}
      />,
    );

    expect(
      screen.queryByTestId("summary-page-signoff-launched"),
    ).toBeInTheDocument();
    // hides signoff not launched section if experiment is launched
    expect(
      screen.queryByTestId("summary-page-signoff-not-launched"),
    ).not.toBeInTheDocument();
  });

  it("does not render signoff launch table if experiment has not been launched", () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.DRAFT,
        }}
      />,
    );

    expect(
      screen.queryByTestId("summary-page-signoff-launched"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("summary-page-signoff-not-launched"),
    ).toBeInTheDocument();
  });

  it("renders the end experiment button if the experiment is live and idle", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
        }}
      />,
    );
    await screen.findByText("End Experiment");
  });

  it("renders the end experiment button if dirty", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
          isRolloutDirty: true,
        }}
      />,
    );
    await screen.findByText("End Experiment");
  });

  it("renders the end enrollment button if dirty", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
          isEnrollmentPaused: false,
          isRolloutDirty: true,
        }}
      />,
    );
    await screen.findByTestId("end-enrollment-start");
  });

  it("renders the cancel review button if the experiment is in review state", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
        }}
      />,
    );
    await screen.findByText("Cancel Review");
  });

  it("does not renders the end experiment button if the experiment is live and not idle", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
        }}
      />,
    );
    expect(screen.queryByText("End Experiment")).not.toBeInTheDocument();
    expect(
      screen.queryByText("End Enrollment for Experiment"),
    ).not.toBeInTheDocument();
  });

  describe("ending an experiment request", () => {
    const origWindowOpen = global.window.open;
    let mockWindowOpen: any;

    beforeEach(() => {
      mockWindowOpen = jest.fn();
      global.window.open = mockWindowOpen;
    });

    afterEach(() => {
      global.window.open = origWindowOpen;
    });

    it("can mark the experiment as requesting review on end confirmation", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          status: NimbusExperimentStatusEnum.LIVE,
          statusNext: NimbusExperimentStatusEnum.COMPLETE,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("can cancel review when the experiment is in review state", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.IDLE,
        {
          statusNext: NimbusExperimentStatusEnum.LIVE,
          changelogMessage: CHANGELOG_MESSAGES.CANCEL_REVIEW,
          isEnrollmentPaused: false,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );

      await screen.findByTestId("cancel-review-start");
      fireEvent.click(screen.getByTestId("cancel-review-start"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("can cancel review for live rollout", async () => {
      const refetch = jest.fn();
      const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
        statusNext: null,
        isEnrollmentPaused: false,
        isRolloutDirty: true,
      });

      const mutationMock = createMutationMock(
        rollout.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          statusNext: NimbusExperimentStatusEnum.LIVE,
          changelogMessage: CHANGELOG_MESSAGES.CANCEL_REVIEW,
          isEnrollmentPaused: false,
        },
      );

      render(
        <Subject
          props={rollout}
          mocks={[mockRollout, mutationMock]}
          {...{ refetch }}
        />,
      );

      await screen.findByTestId("cancel-review-start");
      fireEvent.click(screen.getByTestId("cancel-review-start"));

      screen.queryByTestId("request-update-button");
    });

    it("handles submission with server API error", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        { changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END },
      );
      mutationMock.result.errors = [new Error("Boo")];
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(SUBMIT_ERROR);
    });

    it("handles submission with server-side validation errors", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          statusNext: NimbusExperimentStatusEnum.COMPLETE,
          status: NimbusExperimentStatusEnum.LIVE,
        },
      );
      const errorMessage = "Something went very wrong.";
      mutationMock.result.data.updateExperiment.message = {
        status: [errorMessage],
      };
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(errorMessage);
    });
  });

  describe("ending enrollment for an experiment request", () => {
    const origWindowOpen = global.window.open;
    let mockWindowOpen: any;

    beforeEach(() => {
      mockWindowOpen = jest.fn();
      global.window.open = mockWindowOpen;
    });

    afterEach(() => {
      global.window.open = origWindowOpen;
    });

    it("can mark the experiment as requesting review on enrollment end confirmation", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        statusNext: null,
        isEnrollmentPaused: false,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          status: NimbusExperimentStatusEnum.LIVE,
          statusNext: NimbusExperimentStatusEnum.LIVE,
          isEnrollmentPaused: true,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("handles submission with server API error", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
        },
      );
      mutationMock.result.errors = [new Error("Boo")];
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(SUBMIT_ERROR);
    });

    it("handles submission with server-side validation errors", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          statusNext: NimbusExperimentStatusEnum.LIVE,
          status: NimbusExperimentStatusEnum.LIVE,
          isEnrollmentPaused: true,
        },
      );
      const errorMessage = "Something went very wrong.";
      mutationMock.result.data.updateExperiment.message = {
        status: [errorMessage],
      };
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(errorMessage);
    });
  });

  it("handles dirty Live to Review as expected", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
      statusNext: null,
      isEnrollmentPaused: false,
      isRolloutDirty: true,
    });

    const mutationMock = createMutationMock(
      rollout.id!,
      NimbusExperimentPublishStatusEnum.DIRTY,
      {
        changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_UPDATE,
        statusNext: null,
        publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
        status: NimbusExperimentStatusEnum.LIVE,
      },
    );
    render(<Subject props={rollout} mocks={[mockRollout, mutationMock]} />);
    const requestUpdateButton = await screen.findByTestId(
      "update-live-to-review",
    );
    const endExperimentButton = await screen.findByTestId(
      "end-experiment-start",
    );
    await waitFor(() => {
      expect(requestUpdateButton).toBeInTheDocument();
      expect(endExperimentButton).toBeInTheDocument();
    });
    await act(async () => void fireEvent.click(requestUpdateButton));
  });

  it("shows update and end experiment button for live dirty rollout", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
      statusNext: null,
      isEnrollmentPaused: false,
      isRolloutDirty: true,
    });

    const mutationMock = createMutationMock(
      rollout.id!,
      NimbusExperimentPublishStatusEnum.DIRTY,
      {
        changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_UPDATE,
        statusNext: null,
        publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
        status: NimbusExperimentStatusEnum.LIVE,
      },
    );
    render(<Subject props={rollout} mocks={[mockRollout, mutationMock]} />);
    const requestUpdateButton = await screen.findByTestId(
      "update-live-to-review",
    );
    const endExperimentButton = await screen.findByTestId(
      "end-experiment-start",
    );
    await waitFor(() => {
      expect(requestUpdateButton).toBeInTheDocument();
      expect(endExperimentButton).toBeInTheDocument();
    });
  });

  it("do not show end enrollment button for live dirty rollout", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
      statusNext: null,
      isEnrollmentPaused: false,
      isRolloutDirty: true,
    });

    const mutationMock = createMutationMock(
      rollout.id!,
      NimbusExperimentPublishStatusEnum.DIRTY,
      {
        changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_UPDATE,
        statusNext: null,
        publishStatus: NimbusExperimentPublishStatusEnum.DIRTY,
        status: NimbusExperimentStatusEnum.LIVE,
      },
    );
    render(<Subject props={rollout} mocks={[mockRollout, mutationMock]} />);
    await waitFor(() => {
      expect(
        screen.queryByTestId("end-enrollment-start"),
      ).not.toBeInTheDocument();
    });
  });
});
