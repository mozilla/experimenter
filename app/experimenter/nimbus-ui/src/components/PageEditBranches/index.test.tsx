/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, waitFor, render, fireEvent } from "@testing-library/react";
import PageEditBranches from ".";
import FormBranches from "../FormBranches";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";

describe("PageEditBranches", () => {
  const origConsole = console.log;

  beforeEach(() => {
    console.log = jest.fn();
  });

  afterEach(() => {
    console.log = origConsole;
  });

  it("renders as expected with experiment data", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("feature-config")).toBeInTheDocument();
    for (const feature of MOCK_CONFIG!.featureConfig!) {
      const { slug } = feature!;
      expect(screen.getByText(slug)).toBeInTheDocument();
    }
  });

  it("handles onSave from FormBranches", async () => {
    const { mock, data: experiment } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });
    fireEvent.click(await screen.findByTestId("save-button"));
    expect(console.log).toHaveBeenCalledWith("SAVE", {
      equalRatio: true,
      featureConfig: experiment!.featureConfig,
      referenceBranch: experiment!.referenceBranch,
      treatmentBranches: experiment!.treatmentBranches,
    });
  });

  it("handles onNext from FormBranches", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("next-button"));
    expect(console.log).toHaveBeenCalledWith("NEXT");
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
    featureConfig,
    onSave,
    onNext,
  }: React.ComponentProps<typeof FormBranches>) => {
    const saveState = {
      equalRatio: true,
      featureConfig: experiment.featureConfig,
      referenceBranch: experiment.referenceBranch,
      treatmentBranches: experiment.treatmentBranches,
    };
    return (
      <div data-testid="FormBranches">
        {experiment && (
          <span data-testid="experiment-slug">{experiment.slug}</span>
        )}
        {featureConfig && (
          <ul data-testid="feature-config">
            {featureConfig.map(
              (feature, idx) =>
                feature && <li key={`feature-${idx}`}>{feature.slug}</li>,
            )}
          </ul>
        )}
        <button data-testid="next-button" onClick={() => onNext()}>
          Next
        </button>
        <button
          data-testid="save-button"
          type="submit"
          onClick={() => onSave(saveState)}
        >
          <span>Save</span>
        </button>
      </div>
    );
  },
}));
