/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import HeaderExperiment from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../types/globalTypes";
import AppLayout from "../AppLayout";

const { experiment } = mockExperimentQuery("demo-slug");

storiesOf("components/HeaderExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("status: draft with parent", () => (
    <AppLayout>
      <HeaderExperiment
        parent={{
          ...experiment,
          name: "Example Parent",
          slug: "example-parent",
        }}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("status: preview", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.PREVIEW })}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("publish status: review", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({
          publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
        })}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("status: live", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={null}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.LIVE })}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("status: complete", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.COMPLETE })}
        isArchived={false}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("archived", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.COMPLETE })}
        isArchived={true}
        isRollout={false}
      />
    </AppLayout>
  ))
  .add("rollout", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.COMPLETE })}
        isArchived={false}
        isRollout={true}
      />
    </AppLayout>
  ))
  .add("archived rollout", () => (
    <AppLayout>
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.COMPLETE })}
        isArchived={true}
        isRollout={true}
      />
    </AppLayout>
  ));
