/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { FormAudience } from "src/components/PageEditAudience/FormAudience";
import {
  MockedCache,
  mockExperimentQuery,
  mockLiveRolloutQuery,
  MOCK_CONFIG,
  MOCK_EXPERIMENTS_BY_APPLICATION,
} from "src/lib/mocks";
import { getAllExperimentsByApplication_experimentsByApplication } from "src/types/getAllExperimentsByApplication";
import { getConfig_nimbusConfig } from "src/types/getConfig";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

export const Subject = ({
  config = MOCK_CONFIG,
  experiment = MOCK_EXPERIMENT,
  experimentsByApplication,
  submitErrors = {},
  isLoading = false,
  isServerValid = true,
  onSubmit = () => {},
}: {
  config?: getConfig_nimbusConfig;
  experimentsByApplication?: Partial<{
    allExperiments?: typeof MOCK_EXPERIMENTS_BY_APPLICATION;
    application?: NimbusExperimentApplicationEnum;
  }>;
  allExperimentMeta?: getAllExperimentsByApplication_experimentsByApplication[];
  allExperimentMetaApplication?: NimbusExperimentApplicationEnum;
} & Partial<React.ComponentProps<typeof FormAudience>>) => {
  const [submitErrorsDefault, setSubmitErrors] =
    useState<SerializerMessages>(submitErrors);
  return (
    <div className="p-5">
      <MockedCache {...{ config, experimentsByApplication }}>
        <FormAudience
          submitErrors={submitErrorsDefault}
          {...{
            experiment,
            setSubmitErrors,
            isLoading,
            isServerValid,
            onSubmit,
          }}
        />
      </MockedCache>
    </div>
  );
};

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug").experiment;
export const MOCK_ROLLOUT = mockLiveRolloutQuery("demo-slug").rollout;
