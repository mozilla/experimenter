/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageRequestReview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { createMutationMock } from "./mocks";

const { mock, experiment } = mockExperimentQuery("demo-slug");

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("success", () => (
    <RouterSlugProvider mocks={[mock, createMutationMock(experiment.id!)]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ))
  .add("error", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ))
  .add("non-reviewable", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });

    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageRequestReview polling={false} />
      </RouterSlugProvider>
    );
  });
