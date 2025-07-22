/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ProgressBar from "react-bootstrap/ProgressBar";
import ReactTooltip from "react-tooltip";
import NotSet from "src/components/NotSet";
import { ReactComponent as Info } from "src/images/info.svg";
import { TOOLTIP_DURATION } from "src/lib/constants";
import { humanDate } from "src/lib/dateUtils";
import { getStatus, StatusCheck } from "src/lib/experiment";
import { pluralize } from "src/lib/utils";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

const SummaryTimeline = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => {
  const status = getStatus(experiment);

  return (
    <div className="mb-4" data-testid="summary-timeline">
      <StartEnd
        {...{
          status,
          startDate: experiment.startDate,
          proposedReleaseDate: experiment.isFirstRun
            ? experiment.proposedReleaseDate
            : null,
          computedEnrollmentEndDate: experiment.computedEnrollmentEndDate,
          computedEndDate: experiment.computedEndDate,
          isRollout: experiment.isRollout,
        }}
      />

      <Progress
        {...{
          status,
          startDate: experiment.startDate,
          computedEndDate: experiment.computedEndDate,
        }}
      />

      <Duration
        {...{
          duration: experiment.computedDurationDays,
          enrollment: experiment.computedEnrollmentDays,
          isRollout: experiment.isRollout,
        }}
      />
    </div>
  );
};

const StartEnd = ({
  status,
  startDate,
  proposedReleaseDate,
  computedEnrollmentEndDate,
  computedEndDate,
  isRollout,
}: {
  status: StatusCheck;
  startDate: string | null;
  proposedReleaseDate: string | null;
  computedEnrollmentEndDate: string | null;
  computedEndDate: string | null;
  isRollout: boolean | null;
}) => (
  <div className="d-flex">
    {status.draft || status.preview ? (
      <span className="flex-fill" data-testid="label-not-launched">
        Not yet launched
      </span>
    ) : (
      <>
        <span className="flex-fill" data-testid="label-start-date">
          Start: <b>{humanDate(startDate!)}</b>
        </span>
        {proposedReleaseDate && (
          <span
            className="flex-fill text-center"
            data-testid="label-release-date"
          >
            Release date: <b>{humanDate(proposedReleaseDate!)}</b>
          </span>
        )}
        {computedEnrollmentEndDate && !isRollout && (
          <span
            className="flex-fill text-center"
            data-testid="label-enrollment-end-date"
          >
            Enrollment End: <b>{humanDate(computedEnrollmentEndDate!)}</b>
          </span>
        )}
        {computedEndDate && (
          <span className="flex-fill text-right" data-testid="label-end-date">
            End: <b>{humanDate(computedEndDate!)}</b>
          </span>
        )}
      </>
    )}
  </div>
);

const Progress = ({
  status,
  startDate,
  computedEndDate,
}: {
  status: StatusCheck;
  startDate: string | null;
  computedEndDate: string | null;
}) => {
  const props: React.ComponentProps<typeof ProgressBar> = {
    style: { height: 5 },
    className: "my-2",
  };

  if (status.complete) {
    Object.assign(props, {
      variant: "success",
      now: 100,
    });
  } else if (status.waiting || status.live) {
    Object.assign(props, {
      striped: true,
      animated: true,
      min: Date.parse(startDate!),
      max: Date.parse(computedEndDate!),
      now: Math.min(Date.now(), Date.parse(computedEndDate!)),
    });
  }

  return <ProgressBar {...props} data-testid="timeline-progress-bar" />;
};

const Duration = ({
  duration,
  enrollment,
  isRollout,
}: {
  duration: number | null;
  enrollment: number | null;
  isRollout: boolean | null;
}) => (
  <span>
    Total duration:{" "}
    {duration !== null ? (
      <>
        <b data-testid="label-duration-days">{pluralize(duration, "day")}</b>
        <Info
          data-tip={TOOLTIP_DURATION}
          data-testid="tooltip-duration-summary"
          width="20"
          height="20"
          className="ml-1"
        />
        <ReactTooltip />
      </>
    ) : (
      <NotSet data-testid="label-duration-not-set" />
    )}
    {!isRollout && (
      <>
        {" "}
        / Enrollment:{" "}
        {enrollment !== null ? (
          <b data-testid="label-enrollment-days">
            {pluralize(enrollment, "day")}
          </b>
        ) : (
          <NotSet data-testid="label-enrollment-not-set" />
        )}
      </>
    )}
  </span>
);

export default SummaryTimeline;
