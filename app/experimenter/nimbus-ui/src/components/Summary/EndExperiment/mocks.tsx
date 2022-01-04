/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import EndExperiment from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { getExperiment } from "../../../types/getExperiment";
import { NimbusExperimentStatusEnum } from "../../../types/globalTypes";

export const Subject = ({
  experiment: overrides = {},
  isLoading = false,
  onSubmit = () => {},
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
  isLoading?: boolean;
  onSubmit?: () => void;
}) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatusEnum.LIVE,
    ...overrides,
  });

  return <EndExperiment {...{ experiment, isLoading, onSubmit }} />;
};
