/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import HeaderExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { data } = mockExperimentQuery("demo-slug");

storiesOf("components/HeaderExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => (
    <AppLayout>
      <HeaderExperiment
        name={data!.name}
        slug={data!.slug}
        status={data!.status}
      />
    </AppLayout>
  ))
  .add("status: review", () => (
    <AppLayout>
      <HeaderExperiment
        name={data!.name}
        slug={data!.slug}
        status={NimbusExperimentStatus.REVIEW}
      />
    </AppLayout>
  ))
  .add("status: live", () => (
    <AppLayout>
      <HeaderExperiment
        name={data!.name}
        slug={data!.slug}
        status={NimbusExperimentStatus.LIVE}
      />
    </AppLayout>
  ))
  .add("status: complete", () => (
    <AppLayout>
      <HeaderExperiment
        name={data!.name}
        slug={data!.slug}
        status={NimbusExperimentStatus.COMPLETE}
      />
    </AppLayout>
  ));
