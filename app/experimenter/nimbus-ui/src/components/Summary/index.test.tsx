/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import Summary from ".";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";

describe("Summary", () => {
  it("renders expected components", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject {...{ experiment }} />);
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches (2)",
    );
  });

  it("renders as expected with no defined branches", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(
      <Subject
        experiment={{
          ...experiment,
          referenceBranch: null,
          treatmentBranches: null,
        }}
      />,
    );
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(0);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches (0)",
    );
  });

  describe("JSON representation link", () => {
    it("renders when status is not 'draft' or 'review'", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.ACCEPTED,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("link-json")).toBeInTheDocument();
      expect(screen.getByTestId("link-json")).toHaveAttribute(
        "href",
        "/api/v6/experiments/demo-slug/",
      );
    });
  });

  it("does not render in 'draft' status", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject {...{ experiment }} />);
    expect(screen.queryByTestId("link-json")).not.toBeInTheDocument();
  });

  it("does not render in 'review' status", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject {...{ experiment }} />);
    expect(screen.queryByTestId("link-json")).not.toBeInTheDocument();
  });
});

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <MockedCache>
    <Summary {...{ experiment }} />
  </MockedCache>
);
