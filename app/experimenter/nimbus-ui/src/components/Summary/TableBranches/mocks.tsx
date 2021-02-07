/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import TableBranches from ".";
import {
  MockExperimentContextProvider,
  mockExperimentQuery,
} from "../../../lib/mocks";
import { getExperiment } from "../../../types/getExperiment";
import AppLayout from "../../AppLayout";

type TableBranchesProps = React.ComponentProps<typeof TableBranches>;

const { experiment } = mockExperimentQuery("demo-slug", {});
export const MOCK_EXPERIMENT = {
  ...experiment,
  featureConfig: {
    ...experiment.featureConfig!,
    schema: "{}",
  },
};

export const Subject = ({
  experiment: overrides = {},
}: // experiment = MOCK_EXPERIMENT,
Partial<TableBranchesProps> & {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
}) => (
  <MockExperimentContextProvider {...{ overrides }}>
    <AppLayout>
      <TableBranches />
    </AppLayout>
  </MockExperimentContextProvider>
);
