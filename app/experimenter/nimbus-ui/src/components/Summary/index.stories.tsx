/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import Summary from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

storiesOf("components/Summary", module)
  .add("draft status", () => {
    const { data } = mockExperimentQuery("demo-slug");
    return (
      <Subject>
        <Summary experiment={data!} />
      </Subject>
    );
  })
  .add("non-draft status", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });
    return (
      <Subject>
        <Summary experiment={data!} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
