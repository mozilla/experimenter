/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import LinkNavSummary from ".";
import { mockGetStatus } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";

type SubjectProps = {
  status?: NimbusExperimentStatus;
  statusNext?: NimbusExperimentStatus | null;
  publishStatus?: NimbusExperimentPublishStatus;
  isEnrollmentPausePending?: boolean;
  canReview?: boolean;
  showSummaryAction?: boolean;
};

const Subject = ({
  status = NimbusExperimentStatus.DRAFT,
  statusNext = null,
  publishStatus = NimbusExperimentPublishStatus.IDLE,
  isEnrollmentPausePending = false,
  showSummaryAction = true,
  canReview = false,
}: SubjectProps) => (
  <LinkNavSummary
    slug="my-beautiful-slug"
    status={mockGetStatus({
      status,
      statusNext,
      publishStatus,
      isEnrollmentPausePending,
    })}
    {...{ showSummaryAction, canReview }}
  />
);

describe("LinkNavSummary", () => {
  it("renders 'Request Launch' when expected", () => {
    render(<Subject />);
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("Request Launch")).toBeInTheDocument();
  });

  it("doesn't render action text when 'showSummaryAction' is falsey", () => {
    render(<Subject showSummaryAction={false} />);
    expect(screen.queryByText("Summary")).toBeInTheDocument();
    expect(screen.queryByText("Request Launch")).not.toBeInTheDocument();
  });

  it("renders 'Request Launch' when expected", () => {
    render(<Subject />);
    expect(screen.getByText("Request Launch")).toBeInTheDocument();
  });

  describe("user cannot review", () => {
    it("renders 'Requested Launch' when expected", () => {
      render(<Subject publishStatus={NimbusExperimentPublishStatus.REVIEW} />);
      expect(screen.getByText("Requested Launch")).toBeInTheDocument();
    });

    it("renders 'Requested End' when expected", () => {
      render(
        <Subject
          status={NimbusExperimentStatus.LIVE}
          statusNext={NimbusExperimentStatus.COMPLETE}
          publishStatus={NimbusExperimentPublishStatus.REVIEW}
        />,
      );
      expect(screen.getByText("Requested End")).toBeInTheDocument();
    });

    it("renders 'Requested End Enrollment' when expected", () => {
      render(
        <Subject
          status={NimbusExperimentStatus.LIVE}
          statusNext={NimbusExperimentStatus.LIVE}
          publishStatus={NimbusExperimentPublishStatus.REVIEW}
          isEnrollmentPausePending={true}
        />,
      );
      expect(screen.getByText("Requested End Enrollment")).toBeInTheDocument();
    });
  });

  describe("user can review", () => {
    it("renders 'Review End Request' when expected", () => {
      render(
        <Subject
          status={NimbusExperimentStatus.LIVE}
          statusNext={NimbusExperimentStatus.COMPLETE}
          publishStatus={NimbusExperimentPublishStatus.REVIEW}
          canReview
        />,
      );
      expect(screen.getByText("Review End Request")).toBeInTheDocument();
    });

    it("renders 'Review Launch Request' when expected", () => {
      render(
        <Subject
          publishStatus={NimbusExperimentPublishStatus.REVIEW}
          canReview
        />,
      );
      expect(screen.getByText("Review Launch Request")).toBeInTheDocument();
    });

    it("renders 'Review End Enrollment Request' when expected", () => {
      render(
        <Subject
          status={NimbusExperimentStatus.LIVE}
          statusNext={NimbusExperimentStatus.LIVE}
          publishStatus={NimbusExperimentPublishStatus.REVIEW}
          isEnrollmentPausePending={true}
          canReview
        />,
      );
      expect(
        screen.getByText("Review End Enrollment Request"),
      ).toBeInTheDocument();
    });
  });
});
