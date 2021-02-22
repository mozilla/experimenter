/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import classNames from "classnames";
import React from "react";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { ReactComponent as Clipboard } from "../../images/clipboard.svg";
import { ReactComponent as Cog } from "../../images/cog.svg";
import { BASE_PATH } from "../../lib/constants";
import { humanDate, stringDateSubtract } from "../../lib/dateUtils";
import { StatusCheck } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import "./index.scss";

type HeaderExperimentProps = Pick<
  getExperiment_experimentBySlug,
  "name" | "slug" | "startDate" | "computedEndDate"
> & { status: StatusCheck; summaryView?: boolean };

const HeaderExperiment = ({
  name,
  slug,
  startDate = "",
  computedEndDate = "",
  status,
  summaryView = false,
}: HeaderExperimentProps) => (
  <header className="border-bottom" data-testid="header-experiment">
    {summaryView && (
      <Link
        to={BASE_PATH}
        data-sb-kind="pages/Home"
        className="mb-3 small font-weight-bold d-flex align-items-center"
        data-testid="experiment-return"
      >
        <ChevronLeft className="ml-n1" width="18" height="18" />
        Back to Experiments
      </Link>
    )}

    <h1 className="h5 font-weight-normal" data-testid="header-experiment-name">
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
        {summaryView && status.draft && (
          <StatusLink
            to="edit"
            label="Edit Experiment"
            storiesOf="pages/PageEdit"
            Icon={Cog}
          />
        )}

        {summaryView && status.preview && (
          <StatusLink
            to="request-review"
            label="Go to Review"
            storiesOf="pages/RequestReview"
            Icon={Clipboard}
          />
        )}

        {summaryView && status.preparation && (
          <StatusLink
            to="request-review"
            label="Go to Review"
            storiesOf="pages/RequestReview"
            Icon={Clipboard}
          />
        )}

        {summaryView && status.released && (
          <StatusLink
            to="design"
            label="Go to Design"
            storiesOf="pages/Design"
            Icon={Cog}
          />
        )}

        <p className="header-experiment-status position-relative mt-2 d-inline-block">
          <StatusPill label="Draft" active={status.draft} />
          {status.preview && <StatusPill label="Preview" active />}
          <StatusPill
            label="Review"
            active={status.review || status.accepted}
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
              ({stringDateSubtract(computedEndDate!, startDate!)})
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

const StatusLink = ({
  to,
  storiesOf,
  label,
  Icon,
}: {
  to: string;
  storiesOf: string;
  label: string;
  Icon: React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
}) => (
  <Link
    {...{ to }}
    className="mr-2 pr-2 border-right"
    data-sb-kind={storiesOf}
    data-testid="status-link"
  >
    <Icon className="align-middle mr-1 mb-1" />
    <span className="align-middle mb-1 d-inline-block">{label}</span>
  </Link>
);

export default HeaderExperiment;
