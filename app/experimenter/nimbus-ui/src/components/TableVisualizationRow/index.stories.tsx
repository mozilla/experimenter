/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { mockExperimentQuery } from "../../lib/mocks";
import TableVisualizationRow from ".";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { DISPLAY_TYPE } from "../../lib/visualization/constants";

const { mock } = mockExperimentQuery("demo-slug");

// TODO: this can use a lot more stories as other tables are built out
storiesOf("visualization/TableVisualizationRow", module)
  .addDecorator(withLinks)
  .add("in Highlights table", () => {
    const MOCK_ANALYSIS = mockAnalysis();
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableVisualizationRow
          key="retained"
          results={MOCK_ANALYSIS.overall.control}
          tableLabel="highlights"
          metricKey="retained"
          displayType={DISPLAY_TYPE.POPULATION}
        />
      </RouterSlugProvider>
    );
  });
