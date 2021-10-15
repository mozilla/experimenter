/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useMemo } from "react";
import { ProgressBar } from "react-bootstrap";
import ReactTooltip from "react-tooltip";
import { ReactComponent as Info } from "../../images/info.svg";
import {
  BASE_PATH,
  TOOLTIP_DURATION_AND_ENROLLMENT,
} from "../../lib/constants";
import { humanDate } from "../../lib/dateUtils";
import { StatusCheck } from "../../lib/experiment";
import { pluralize } from "../../lib/utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import "./index.scss";

type HeaderExperimentProps = Pick<
  getExperiment_experimentBySlug,
  | "name"
  | "slug"
  | "parent"
  | "startDate"
  | "computedEndDate"
  | "computedDurationDays"
  | "computedEnrollmentDays"
  | "enrollmentEndDate"
  | "isArchived"
  | "isEnrollmentPaused"
> & { status: StatusCheck };

const HeaderExperiment = ({
  name,
  slug,
  parent,
  startDate = "",
  computedEndDate = "",
  computedDurationDays,
  computedEnrollmentDays,
  enrollmentEndDate,
  status,
  isArchived,
  isEnrollmentPaused,
}: HeaderExperimentProps) => (
  <header className="border-bottom" data-testid="header-experiment">
    <h1
      className="h5 font-weight-normal d-inline"
      data-testid="header-experiment-name"
    >
      {name}
    </h1>
    {isArchived && (
      <StatusPill
        className="ml-2"
        label="Archived"
        color="danger"
        active={true}
        testid="header-experiment-status-archived"
      />
    )}
    {status.live && !isEnrollmentPaused && (
      <StatusPill
        testid="pill-enrolling-active"
        className="ml-2"
        color="primary"
        active={true}
        label="Enrolling Users in Progress"
      />
    )}
    {status.live && isEnrollmentPaused && enrollmentEndDate && (
      <StatusPill
        testid="pill-enrolling-complete"
        className="ml-2"
        color="primary"
        active={true}
        label="Enrollment Complete"
      />
    )}
    <p
      className="text-monospace text-secondary mb-1 small"
      data-testid="header-experiment-slug"
    >
      {slug}
    </p>
    {parent && (
      <p
        className="text-secondary mb-1 small"
        data-testid="header-experiment-parent"
      >
        Cloned from <a href={`${BASE_PATH}/${parent.slug}`}>{parent.name}</a>
      </p>
    )}
    <div className="row header-experiment-status align-items-center position-relative mx-0 mt-2 mb-4">
      <StatusPill label="Draft" active={status.draft && status.idle} />
      {status.preview && status.idle && <StatusPill label="Preview" active />}
      <StatusPill
        label="Review"
        active={(status.draft || status.preview) && !status.idle}
      />
      <StatusPill label="Live" active={status.live} />
      <StatusTimeline
        {...{
          status,
          startDate,
          computedEndDate,
          computedDurationDays,
          computedEnrollmentDays,
        }}
      />
      <StatusPill label="Complete" active={status.complete} padded={false} />
    </div>
  </header>
);

const StatusTimeline = ({
  status,
  startDate,
  computedEndDate,
  computedDurationDays,
  computedEnrollmentDays,
}: {
  status: StatusCheck;
  startDate: string | null;
  computedEndDate: string | null;
  computedDurationDays: number | null;
  computedEnrollmentDays: number | null;
}) => {
  const progressBarProps = useMemo(() => {
    if (status.live) {
      return {
        striped: true,
        animated: true,
        min: Date.parse(startDate!),
        max: Date.parse(computedEndDate!),
        now: Math.min(Date.now(), Date.parse(computedEndDate!)),
      };
    }
    if (status.complete) {
      return { variant: "success", now: 100 };
    }
    return { now: 0 };
  }, [status, startDate, computedEndDate]);

  return (
    <span className="col flex-grow-2 p-0 mr-3 text-center position-relative">
      <ProgressBar
        {...{ style: { height: 18 }, ...progressBarProps }}
        data-testid="header-progress-bar"
      />
      {!(status.draft || status.preview) && (
        <>
          <small
            className="font-weight-bold position-absolute"
            style={{ left: 0 }}
          >
            {humanDate(startDate!)}
          </small>
          <small
            className="font-weight-bold position-absolute"
            style={{ right: 0 }}
          >
            {computedEndDate ? humanDate(computedEndDate!) : "Present"}
          </small>
        </>
      )}

      {computedDurationDays && (
        <small className="position-absolute">
          {computedEnrollmentDays && (
            <>
              {pluralize(computedEnrollmentDays, "day")}
              {" / "}
            </>
          )}
          {pluralize(computedDurationDays, "day")}
          <Info
            data-tip={TOOLTIP_DURATION_AND_ENROLLMENT}
            data-testid="tooltip-duration-summary"
            width="20"
            height="20"
            className="ml-1"
          />
          <ReactTooltip />
        </small>
      )}
    </span>
  );
};

const StatusPill = ({
  label,
  active,
  padded = true,
  color = "primary",
  className = "",
  testid = "",
}: {
  label: string;
  active: boolean;
  padded?: boolean;
  color?: string;
  className?: string;
  testid?: string;
}) => (
  <span
    className={
      classNames(
        `col flex-grow-0 border rounded-pill px-2 bg-white status-${label}`,
        active ? `border-${color} text-${color}` : "border-muted text-muted",
        padded && "mr-3",
      ) +
      " " +
      className
    }
    data-testid={
      testid ||
      (active ? "header-experiment-status-active" : "header-experiment-status")
    }
  >
    {label}
  </span>
);

export default HeaderExperiment;
