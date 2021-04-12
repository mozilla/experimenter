/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import AppLayoutWithExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";

storiesOf("components/AppLayoutWithExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => {
    const { mock } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <AppLayoutWithExperiment
          title="Howdy!"
          testId="AppLayoutWithExperiment"
        >
          {({ experiment }) => <p>{experiment.name}</p>}
        </AppLayoutWithExperiment>
      </RouterSlugProvider>
    );
  })
  .add("status: preview", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <AppLayoutWithExperiment
          title="Howdy!"
          testId="AppLayoutWithExperiment"
        >
          {({ experiment }) => <p>{experiment.name}</p>}
        </AppLayoutWithExperiment>
      </RouterSlugProvider>
    );
  })
  .add('status: launched ("live" or "complete")', () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <AppLayoutWithExperiment
          title="Howdy!"
          testId="AppLayoutWithExperiment"
        >
          {({ experiment }) => <p>{experiment.name}</p>}
        </AppLayoutWithExperiment>
      </RouterSlugProvider>
    );
  })
  .add("publish status: review", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <AppLayoutWithExperiment
          title="Howdy!"
          testId="AppLayoutWithExperiment"
        >
          {({ experiment }) => <p>{experiment.name}</p>}
        </AppLayoutWithExperiment>
      </RouterSlugProvider>
    );
  });
