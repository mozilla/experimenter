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
const { name, slug } = experiment;
const status = mockGetStatus(experiment);

const ONE_DAY = 24 * 60 * 60 * 1000;
const then = Date.now() - 7 * ONE_DAY;
const startDate = new Date(then).toISOString();
const computedDurationDays = 24;
const computedEnrollmentDays = 5;
const computedEndDate = new Date(
  then + computedDurationDays * ONE_DAY,
).toISOString();

const commonHeaderExperimentProps: React.ComponentProps<
  typeof HeaderExperiment
> = {
  parent: null,
  name,
  slug,
  status,
  isArchived: false,
  startDate,
  computedEndDate,
  computedDurationDays,
  computedEnrollmentDays,
};

storiesOf("components/HeaderExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => (
    <AppLayout>
      <HeaderExperiment {...commonHeaderExperimentProps} />
    </AppLayout>
  ))
  .add("status: draft with parent", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        parent={{
          ...experiment,
          name: "Example Parent",
          slug: "example-parent",
        }}
      />
    </AppLayout>
  ))
  .add("status: preview", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        status={mockGetStatus({ status: NimbusExperimentStatus.PREVIEW })}
      />
    </AppLayout>
  ))
  .add("publish status: review", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        status={mockGetStatus({
          publishStatus: NimbusExperimentPublishStatus.REVIEW,
        })}
      />
    </AppLayout>
  ))
  .add("status: live", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />
    </AppLayout>
  ))
  .add("status: complete", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        status={mockGetStatus({ status: NimbusExperimentStatus.COMPLETE })}
      />
    </AppLayout>
  ))
  .add("archived", () => (
    <AppLayout>
      <HeaderExperiment
        {...commonHeaderExperimentProps}
        status={mockGetStatus({ status: NimbusExperimentStatus.COMPLETE })}
        isArchived={true}
      />
    </AppLayout>
  ));
