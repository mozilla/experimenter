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
    expect(screen.queryByTestId("experiment-end")).not.toBeInTheDocument();
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches (2)",
    );
  });

  it("renders end experiment component if experiment is live", async () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(<Subject {...{ experiment }} />);
    await screen.findByTestId("experiment-end");
  });

  it("renders end experiment badge if end is requested", async () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEndRequested: true,
    });
    render(<Subject {...{ experiment }} />);
    await screen.findByTestId("pill-end-requested");
  });

  it("renders end experiment badge if enrollment is not paused", async () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEnrollmentPaused: false,
    });
    render(<Subject {...{ experiment }} />);
    await screen.findByTestId("pill-enrolling-active");
  });

  it("renders end experiment badge if enrollment is not paused", async () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEnrollmentPaused: true,
      enrollmentEndDate: new Date().toISOString(),
    });
    render(<Subject {...{ experiment }} />);
    await screen.findByTestId("pill-enrolling-complete");
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
    function renderWithStatus(status: NimbusExperimentStatus) {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status,
      });
      render(<Subject {...{ experiment }} />);
    }
    it("renders with the correct API link", () => {
      renderWithStatus(NimbusExperimentStatus.LIVE);
      expect(screen.getByTestId("link-json")).toBeInTheDocument();
      expect(screen.getByTestId("link-json")).toHaveAttribute(
        "href",
        "/api/v6/experiments/demo-slug/",
      );
    });
    it("renders when status is 'review'", () => {
      renderWithStatus(NimbusExperimentStatus.REVIEW);
      expect(screen.queryByTestId("link-json")).toBeInTheDocument();
    });
    it("renders when status is 'accepted'", () => {
      renderWithStatus(NimbusExperimentStatus.ACCEPTED);
      expect(screen.queryByTestId("link-json")).toBeInTheDocument();
    });
    it("does not render in 'draft' status", () => {
      renderWithStatus(NimbusExperimentStatus.DRAFT);
      expect(screen.queryByTestId("link-json")).not.toBeInTheDocument();
    });
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
