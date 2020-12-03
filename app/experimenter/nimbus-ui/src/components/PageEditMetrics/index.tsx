/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormMetrics from "../FormMetrics";
import LinkExternal from "../LinkExternal";
import { useConfig } from "../../hooks/useConfig";

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => {
  const { probeSets } = useConfig();

  return (
    <AppLayoutWithExperiment title="Metrics" testId="PageEditMetrics">
      {({ experiment }) => (
        <>
          <p>
            Every experiment analysis automatically includes how your experiment
            has impacted <strong>Retention, Search Count, and Ad Click</strong>{" "}
            metrics. Get more information on{" "}
            {/* TODO Requires url https://jira.mozilla.com/browse/EXP-656 */}
            <LinkExternal href="">Core Firefox Metrics.</LinkExternal>
          </p>
          <FormMetrics
            {...{
              experiment,
              probeSets,
              isLoading: false,
              isServerValid: true,
              submitErrors: {},
              /* TODO: EXP-505 for accepting and saving edits to branches */
              onSave: async (update) => console.log("SAVE", update),
              onNext: () => console.log("NEXT"),
            }}
          />
        </>
      )}
    </AppLayoutWithExperiment>
  );
};

export default PageEditMetrics;
