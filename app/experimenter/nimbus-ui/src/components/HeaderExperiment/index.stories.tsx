/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import HeaderExperiment from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import AppLayout from "../AppLayout";

const { experiment } = mockExperimentQuery("demo-slug");

storiesOf("components/HeaderExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
      />
    </AppLayout>
  ))
  .add("status: preview", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatus.PREVIEW })}
        isArchived={false}
      />
    </AppLayout>
  ))
  .add("publish status: review", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({
          publishStatus: NimbusExperimentPublishStatus.REVIEW,
        })}
        isArchived={false}
      />
    </AppLayout>
  ))
  .add("status: live", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={null}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
        isArchived={false}
      />
    </AppLayout>
  ))
  .add("status: complete", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatus.COMPLETE })}
        isArchived={false}
      />
    </AppLayout>
  ))
  .add("archived", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatus.COMPLETE })}
        isArchived={true}
      />
    </AppLayout>
  ))
  .add("archived with message", () => (
    <AppLayout>
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatus.COMPLETE })}
        isArchived={true}
        archiveReason="No longer relevant"
      />
    </AppLayout>
  ));
