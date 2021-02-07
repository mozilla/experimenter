/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayoutWithSidebar from ".";
import { MockExperimentContextProvider } from "../../lib/mocks";
import {
  getExperiment,
  getExperiment_experimentBySlug_readyForReview,
} from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";

export const Subject = ({
  status,
  review,
}: {
  status?: NimbusExperimentStatus;
  review?: getExperiment_experimentBySlug_readyForReview;
}) => {
  const overrides: Partial<getExperiment["experimentBySlug"]> = {};

  if (status) {
    overrides.status = status;
  }

  if (review) {
    overrides.readyForReview = review;
  }

  return (
    <MockExperimentContextProvider {...{ overrides }}>
      <AppLayoutWithSidebar>
        <p>Howdy neighbor</p>
      </AppLayoutWithSidebar>
    </MockExperimentContextProvider>
  );
};
