/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React from "react";
import ReactTooltip from "react-tooltip";
import { ReactComponent as Info } from "../../images/info.svg";
import { humanDate } from "../../lib/dateUtils";
import { StatusCheck } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import "./index.scss";

type HeaderExperimentProps = Pick<
  getExperiment_experimentBySlug,
  | "name"
  | "slug"
  | "startDate"
  | "computedEndDate"
  | "computedDurationDays"
  | "isArchived"
> & { archiveReason?: string | null; status: StatusCheck };

const HeaderExperiment = ({
  name,
  slug,
  startDate = "",
  computedEndDate = "",
  status,
  computedDurationDays,
  isArchived,
  archiveReason = "",
}: HeaderExperimentProps) => (
  <header className="border-bottom" data-testid="header-experiment">
    <h1
      className="h5 font-weight-normal d-inline"
      data-testid="header-experiment-name"
    >
      {name}
    </h1>
    {isArchived && (
      <>
        <StatusPill
          className="ml-2"
          label="Archived"
          color="danger"
          active={true}
        />
        {archiveReason!.length > 0 && (
          <>
            <Info
              data-tip={`Archive reason: ${archiveReason}`}
              width="20"
              height="20"
              className="ml-1 text-danger ml-n2 align-text-top"
            />
            <ReactTooltip />
          </>
        )}
      </>
    )}
    <p
      className="text-monospace text-secondary mb-1 small"
      data-testid="header-experiment-slug"
    >
      {slug}
    </p>
    <div className="row">
      <div className="col">
        <p className="header-experiment-status position-relative mt-2 d-inline-block">
          <StatusPill label="Draft" active={status.draft && status.idle} />
          {status.preview && status.idle && (
            <StatusPill label="Preview" active />
          )}
          <StatusPill
            label="Review"
            active={(status.draft || status.preview) && !status.idle}
          />
          <StatusPill label="Live" active={status.live} />
          <StatusPill
            label="Complete"
            active={status.complete}
            padded={false}
          />
        </p>
      </div>
      {(status.live || status.complete) && (
        <div className="text-right col mt-2" data-testid="header-dates">
          <span className="font-weight-bold">{humanDate(startDate!)}</span> to{" "}
          {computedEndDate ? (
            <>
              <span className="font-weight-bold">
                {humanDate(computedEndDate!)}
              </span>{" "}
              ({computedDurationDays} days)
            </>
          ) : (
            <span className="font-weight-bold">Present</span>
          )}
        </div>
      )}
    </div>
  </header>
);

const StatusPill = ({
  label,
  active,
  padded = true,
  color = "primary",
  className = "",
}: {
  label: string;
  active: boolean;
  padded?: boolean;
  color?: string;
  className?: string;
}) => (
  <span
    className={
      classNames(
        "border rounded-pill px-2 bg-white position-relative",
        active ? `border-${color} text-${color}` : "border-muted text-muted",
        padded && "mr-3",
      ) +
      " " +
      className
    }
    data-testid={
      active ? "header-experiment-status-active" : "header-experiment-status"
    }
  >
    {label}
  </span>
);

export default HeaderExperiment;
