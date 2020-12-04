/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { mockExperimentQuery } from "../../lib/mocks";
import TableResults from ".";
import { mockAnalysis } from "../../lib/visualization/mocks";

storiesOf("visualization/TableResults", module)
  .addDecorator(withLinks)
  .add("basic, with one primary probe set", () => {
    const { mock, data } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryProbeSets={data!.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>
    );
  })
  .add("with multiple primary probe sets", () => {
    const { mock, data } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
        {
          __typename: "NimbusProbeSetType",
          id: "2",
          slug: "feature_b",
          name: "Feature B",
        },
        {
          __typename: "NimbusProbeSetType",
          id: "3",
          slug: "feature_c",
          name: "Feature C",
        },
      ],
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryProbeSets={data!.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>
    );
  });
