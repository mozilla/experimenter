/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableResults from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { mockAnalysis } from "../../../lib/visualization/mocks";

storiesOf("pages/Results/TableResults", module)
  .addDecorator(withLinks)
  .add("basic, with one primary probe set", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryOutcomes={experiment.primaryOutcomes!}
          results={mockAnalysis()}
        />
      </RouterSlugProvider>
    );
  })
  .add("with multiple primary probe sets", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: [
        {
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
        {
          slug: "feature_b",
          name: "Feature B",
        },
        {
          slug: "feature_c",
          name: "Feature C",
        },
      ],
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryOutcomes={experiment.primaryOutcomes!}
          results={mockAnalysis()}
        />
      </RouterSlugProvider>
    );
  });
