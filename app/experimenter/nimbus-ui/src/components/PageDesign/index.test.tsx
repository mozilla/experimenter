/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor } from "@testing-library/react";
import PageDesign from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery, MOCK_REVIEW } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";

const { mock, experiment: mockExperiment } = mockExperimentQuery("demo-slug");
const mockAnalysisData: AnalysisData | undefined = mockAnalysis();

describe("PageDesign", () => {
  it("renders as expected", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageDesign />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageDesign")).toBeInTheDocument();
    });
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../AppLayoutWithExperiment", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof AppLayoutWithExperiment>) => (
    <div data-testid="PageDesign">
      {props.children({
        experiment: mockExperiment,
        analysis: mockAnalysisData,
        review: {
          ...MOCK_REVIEW,
        },
      })}
    </div>
  ),
}));
