/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import TableWithTabComparison, { TableWithTabComparisonProps } from ".";
import {
  mockExperimentQuery,
  MockResultsContextProvider,
} from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";

export const Subject = ({
  Table,
  className,
  experiment,
}: TableWithTabComparisonProps) => {
  const { mock } = mockExperimentQuery("demo-slug");
  return (
    <RouterSlugProvider mocks={[mock]}>
      <MockResultsContextProvider>
        <TableWithTabComparison {...{ experiment, Table, className }} />
      </MockResultsContextProvider>
    </RouterSlugProvider>
  );
};
