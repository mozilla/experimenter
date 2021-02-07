/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { Subject } from "./mocks";

storiesOf("components/AppLayoutSidebarLocked", module)
  .addDecorator(withLinks)
  .add("analysis results loading", () => (
    <Subject
      loadingSidebar
      analysis={null}
      experiment={{
        status: NimbusExperimentStatus.LIVE,
        primaryProbeSets: null,
        secondaryProbeSets: null,
      }}
    />
  ))
  .add("analysis results error", () => (
    <Subject
      analysis={null}
      analysisError={new Error("Boop")}
      experiment={{
        primaryProbeSets: null,
        secondaryProbeSets: null,
      }}
    />
  ))
  .add("has analysis results", () => (
    <Subject
      analysis={{
        show_analysis: true,
        daily: [],
        weekly: {},
        overall: {},
        other_metrics: mockAnalysis().other_metrics,
      }}
      experiment={{
        status: NimbusExperimentStatus.COMPLETE,
      }}
    />
  ));
