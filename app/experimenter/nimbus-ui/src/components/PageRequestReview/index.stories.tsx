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
import { mock, Subject } from "./mocks";

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("draft status", () => {
    return <Subject />;
  })
  .add("preview status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("review status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("non-reviewable", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("error", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ));
