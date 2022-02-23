/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import TableBranches from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import AppLayout from "../../AppLayout";

type TableBranchesProps = React.ComponentProps<typeof TableBranches>;

const { experiment } = mockExperimentQuery("demo-slug", {});
export const MOCK_EXPERIMENT: getExperiment_experimentBySlug = {
  ...experiment,
  featureConfigs: experiment.featureConfigs!.map((f) => ({
    ...f!,
    schema: "{}",
  })),
};

export const Subject = ({
  experiment = MOCK_EXPERIMENT,
}: Partial<TableBranchesProps>) => {
  return (
    <AppLayout>
      <RouterSlugProvider>
        <TableBranches {...{ experiment }} />
      </RouterSlugProvider>
    </AppLayout>
  );
};
