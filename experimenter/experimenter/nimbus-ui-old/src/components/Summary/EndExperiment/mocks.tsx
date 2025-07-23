/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import EndExperiment from "src/components/Summary/EndExperiment";
import { mockExperimentQuery } from "src/lib/mocks";
import { getExperiment } from "src/types/getExperiment";
import { NimbusExperimentStatusEnum } from "src/types/globalTypes";

export const Subject = ({
  experiment: overrides = {},
  isLoading = false,
  onSubmit = () => {},
  isRollout = false,
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
  isLoading?: boolean;
  onSubmit?: () => void;
  isRollout?: boolean;
}) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatusEnum.LIVE,
    ...overrides,
  });

  return <EndExperiment {...{ experiment, isLoading, onSubmit, isRollout }} />;
};
