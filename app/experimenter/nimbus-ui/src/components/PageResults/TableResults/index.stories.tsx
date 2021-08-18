/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableResults from ".";
import {
  mockExperimentQuery,
  MockResultsContextProvider,
} from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { BRANCH_COMPARISON } from "../../../lib/visualization/constants";
import { mockIncompleteAnalysis } from "../../../lib/visualization/mocks";

storiesOf("pages/Results/TableResults", module)
  .addDecorator(withLinks)
  .add("relative uplift comparison, with one primary outcome", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>
    );
  })
  .add("relative uplift comparison, with multiple primary outcomes", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["picture_in_picture", "feature_b", "feature_c"],
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>
    );
  })
  .add("absolute uplift comparison, with one primary outcome", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
            {...{ experiment }}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>
    );
  })
  .add("absolute uplift comparison, with multiple primary outcomes", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["picture_in_picture", "feature_b", "feature_c"],
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
            {...{ experiment }}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>
    );
  })
  .add("missing retention with warning", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    return (
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider analysis={mockIncompleteAnalysis()}>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>
    );
  });
