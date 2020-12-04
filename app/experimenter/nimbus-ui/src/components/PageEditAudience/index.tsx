/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useRef } from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useConfig } from "../../hooks";
import FormAudience from "../FormAudience";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const config = useConfig();

  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  // TODO: EXP-506 should call this when the form is saved
  const refetchReview = useRef<() => void>();

  return (
    <AppLayoutWithExperiment title="Audience" testId="PageEditAudience">
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;

        const { isMissingField } = review;

        return (
          <FormAudience
            {...{
              experiment,
              config,
              isMissingField,
            }}
          />
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditAudience;
