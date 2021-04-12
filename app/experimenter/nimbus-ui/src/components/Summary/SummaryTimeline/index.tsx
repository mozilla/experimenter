/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ProgressBar from "react-bootstrap/ProgressBar";
import { humanDate } from "../../../lib/dateUtils";
import { getStatus, StatusCheck } from "../../../lib/experiment";
import pluralize from "../../../lib/pluralize";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import NotSet from "../../NotSet";

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
          computedEndDate: experiment.computedEndDate,
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
          duration: experiment.proposedDuration,
          enrollment: experiment.proposedEnrollment,
        }}
      />
    </div>
  );
};

const StartEnd = ({
  status,
  startDate,
  computedEndDate,
}: {
  status: StatusCheck;
  startDate: string | null;
  computedEndDate: string | null;
}) => (
  <div className="d-flex">
    {status.draft || status.review || status.preview || status.waiting ? (
      <span className="flex-fill" data-testid="label-not-launched">
        Not yet launched
      </span>
    ) : (
      <>
        <span className="flex-fill" data-testid="label-start-date">
          {humanDate(startDate!)}
        </span>
        {computedEndDate && (
          <span className="flex-fill text-right" data-testid="label-end-date">
            {humanDate(computedEndDate!)}
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
}: {
  duration: number | null;
  enrollment: number | null;
}) => (
  <span>
    Total duration:{" "}
    {duration !== null ? (
      <b data-testid="label-duration-days">{pluralize(duration, "day")}</b>
    ) : (
      <NotSet data-testid="label-duration-not-set" />
    )}{" "}
    / Enrollment:{" "}
    {enrollment !== null ? (
      <b data-testid="label-enrollment-days">{pluralize(enrollment, "day")}</b>
    ) : (
      <NotSet data-testid="label-enrollment-not-set" />
    )}
  </span>
);

export default SummaryTimeline;
