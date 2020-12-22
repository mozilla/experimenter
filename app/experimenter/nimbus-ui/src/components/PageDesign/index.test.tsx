/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor } from "@testing-library/react";
import PageDesign from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { getStatus as mockGetStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

let mockExperiment: getExperiment_experimentBySlug;
const mockAnalysisData: AnalysisData | undefined = mockAnalysis();
let redirectPath: string | void;

describe("PageDesign", () => {
  it("renders as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    mockExperiment = experiment;
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageDesign />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageDesign")).toBeInTheDocument();
    });
  });

  it("redirects to the edit overview page if the experiment status is draft", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    mockExperiment = experiment;
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageDesign />
      </RouterSlugProvider>,
    );
    expect(redirectPath).toEqual("edit/overview");
  });

  it("redirects to the edit overview page if the experiment status is review", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    mockExperiment = experiment;
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageDesign />
      </RouterSlugProvider>,
    );
    expect(redirectPath).toEqual("edit/overview");
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../AppLayoutWithExperiment", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof AppLayoutWithExperiment>) => {
    redirectPath = props.redirect!({
      status: mockGetStatus(mockExperiment),
      analysis: mockAnalysisData,
    });

    return (
      <div data-testid="PageDesign">
        {props.children({
          experiment: mockExperiment,
          analysis: mockAnalysisData,
          review: {
            isMissingField: () => false,
            refetch: () => {},
            ready: true,
            invalidPages: [],
            missingFields: [],
          },
        })}
      </div>
    );
  },
}));
