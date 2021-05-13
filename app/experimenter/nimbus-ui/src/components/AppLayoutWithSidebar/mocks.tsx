/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import { AppLayoutWithSidebar } from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

export const Subject = ({
  experiment: overrides,
}: RouteComponentProps & {
  experiment?: Partial<getExperiment_experimentBySlug>;
}) => {
  const { mock, experiment } = mockExperimentQuery(
    "my-special-slug",
    overrides,
  );

  return (
    <RouterSlugProvider mocks={[mock]} path="/my-special-slug/edit">
      <AppLayoutWithSidebar {...{ experiment }}>
        <p data-testid="test-child">Hello, world!</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  );
};
