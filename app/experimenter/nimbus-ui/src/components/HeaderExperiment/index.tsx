/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

type HeaderExperimentProps = Pick<
  getExperiment_experimentBySlug,
  "name" | "slug" | "status"
>;

const HeaderExperiment = ({ name, slug, status }: HeaderExperimentProps) => (
  <header className="border-bottom" data-testid="header-experiment">
    <h1 className="h5 font-weight-normal" data-testid="header-experiment-name">
      {name}
    </h1>
    <p
      className="text-monospace text-secondary mb-1"
      data-testid="header-experiment-slug"
    >
      {slug}
    </p>
    <p data-testid="header-experiment-status">{status}</p>
  </header>
);

export default HeaderExperiment;
