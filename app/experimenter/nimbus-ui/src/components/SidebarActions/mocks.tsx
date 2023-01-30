/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { RouteComponentProps } from "@reach/router";
import React from "react";
import { SidebarActions } from "src/components/SidebarActions";
import { getStatus, StatusCheck } from "src/lib/experiment";
import { mockExperimentQuery } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { AnalysisData } from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export const Subject = ({
  experiment: overrides,
  refetch = async () => {},
  mocks = [],
  status,
  analysis,
}: RouteComponentProps & {
  experiment?: Partial<getExperiment_experimentBySlug>;
  refetch?: () => Promise<any>;
  mocks?: MockedResponse[];
  status?: StatusCheck;
  analysis?: AnalysisData;
}) => {
  const { mock, experiment } = mockExperimentQuery(
    "my-special-slug",
    overrides,
  );

  return (
    <RouterSlugProvider mocks={[mock, ...mocks]} path="/my-special-slug/edit">
      <SidebarActions
        {...{
          experiment,
          refetch,
          analysis,
          status: status || getStatus(experiment),
        }}
      />
    </RouterSlugProvider>
  );
};
