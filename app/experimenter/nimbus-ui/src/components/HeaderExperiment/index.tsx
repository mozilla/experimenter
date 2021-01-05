/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { StatusCheck } from "../../lib/experiment";
import "./index.scss";

type HeaderExperimentProps = Pick<
  getExperiment_experimentBySlug,
  "name" | "slug"
> & { status: StatusCheck };

const HeaderExperiment = ({ name, slug, status }: HeaderExperimentProps) => (
  <header className="border-bottom" data-testid="header-experiment">
    <h1 className="h5 font-weight-normal" data-testid="header-experiment-name">
      {name}
    </h1>
    <p
      className="text-monospace text-secondary mb-1 small"
      data-testid="header-experiment-slug"
    >
      {slug}
    </p>
    <p className="header-experiment-status position-relative mt-2 d-inline-block">
      <StatusPill label="Draft" active={status.draft} />
      <StatusPill label="Review" active={status.review || status.accepted} />
      <StatusPill label="Live" active={status.live} />
      <StatusPill label="Complete" active={status.complete} padded={false} />
    </p>
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

export default HeaderExperiment;
