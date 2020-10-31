/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, waitFor, render } from "@testing-library/react";
import PageEditBranches from ".";
import FormBranches from "../FormBranches";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";

describe("PageEditBranches", () => {
  it("renders as expected with experiment data", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
    expect(screen.getByTestId("equal-ratio")).toHaveTextContent("false");
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("feature-config")).toBeInTheDocument();
    for (const feature of MOCK_CONFIG!.featureConfig!) {
      const { slug } = feature!;
      expect(screen.getByText(slug)).toBeInTheDocument();
    }
  });
});

const Subject = ({
  mocks = [],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageEditBranches />
  </RouterSlugProvider>
);

jest.mock("../FormBranches", () => ({
  __esModule: true,
  default: ({
    experiment,
    equalRatio,
    featureConfig,
  }: React.ComponentProps<typeof FormBranches>) => {
    return (
      <div data-testid="FormBranches">
        {experiment && (
          <span data-testid="experiment-slug">{experiment.slug}</span>
        )}
        <span data-testid="equal-ratio">{equalRatio ? "true" : "false"}</span>
        {featureConfig && (
          <ul data-testid="feature-config">
            {featureConfig.map(
              (feature, idx) =>
                feature && <li key={`feature-${idx}`}>{feature.slug}</li>,
            )}
          </ul>
        )}
      </div>
    );
  },
}));
