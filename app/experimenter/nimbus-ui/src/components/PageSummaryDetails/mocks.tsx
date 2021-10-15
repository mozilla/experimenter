/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageSummaryDetails from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

export const { mock, experiment } = mockExperimentQuery("demo-slug");

export const Subject = ({
  mocks = [mock],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => {
  return (
    <RouterSlugProvider {...{ mocks }}>
      <PageSummaryDetails polling={false} />
    </RouterSlugProvider>
  );
};
