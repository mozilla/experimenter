/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useContext } from "react";
import { ExperimentContext } from "../../lib/contexts";
import { humanDate, stringDateSubtract } from "../../lib/dateUtils";
import "./index.scss";

const HeaderExperiment = () => {
  const { experiment, status } = useContext(ExperimentContext);
  const { name, slug, startDate, endDate } = experiment!;

  return (
    <header className="border-bottom" data-testid="header-experiment">
      <h1
        className="h5 font-weight-normal"
        data-testid="header-experiment-name"
      >
        {name}
      </h1>
      <p
        className="text-monospace text-secondary mb-1 small"
        data-testid="header-experiment-slug"
      >
        {slug}
      </p>
      <div className="row">
        <div className="col">
          <p className="header-experiment-status position-relative mt-2 d-inline-block">
            <StatusPill label="Draft" active={status.draft} />
            {
              /* istanbul ignore next until EXP-866 final */ status.preview && (
                <StatusPill label="Preview" active={status.preview} />
              )
            }
            <StatusPill
              label="Review"
              active={status.review || status.accepted}
            />
            <StatusPill label="Live" active={status!.live} />
            <StatusPill
              label="Complete"
              active={status!.complete}
              padded={false}
            />
          </p>
        </div>
        {(status.live || status.complete) && startDate && (
          <div className="text-right col mt-2" data-testid="header-dates">
            <span className="font-weight-bold">{humanDate(startDate)}</span> to{" "}
            {endDate ? (
              <>
                <span className="font-weight-bold">{humanDate(endDate)}</span> (
                {stringDateSubtract(endDate!, startDate!)})
              </>
            ) : (
              <span className="font-weight-bold">Present</span>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

const StatusPill = ({
  label,
  active,
  padded = true,
}: {
  label: string;
  active: boolean;
  padded?: boolean;
}) => (
  <span
    className={classNames(
      "border rounded-pill px-2 bg-white position-relative",
      active ? "border-primary text-primary" : "border-muted text-muted",
      padded && "mr-3",
    )}
    data-testid={
      active ? "header-experiment-status-active" : "header-experiment-status"
    }
  >
    {label}
  </span>
);

export default HeaderExperiment;
