/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import TableSummary from ".";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

describe("TableSummary", () => {
  describe("renders Experiment Owner row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-owner")).toHaveTextContent(
        "example@mozilla.com",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        owner: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-owner")).toHaveTextContent(
        "Owner not set",
      );
    });
  });
  describe("renders Hypothesis row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-hypothesis")).toHaveTextContent(
        "Realize material say pretty.",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        hypothesis: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-hypothesis")).toHaveTextContent(
        "Hypothesis not set",
      );
    });
  });

  describe("renders Probe Sets row as expected", () => {
    it("when both are set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-probe-primary")).toHaveTextContent(
        "Primary: Picture-in-Picture",
      );
      expect(
        screen.getByTestId("experiment-probe-secondary"),
      ).toHaveTextContent(
        "Secondary: Public-key intangible Graphical User Interface",
      );
    });
    it("when neither are set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        primaryProbeSets: [],
        secondaryProbeSets: [],
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-probe-primary")).toHaveTextContent(
        "Primary: probe not set",
      );
      expect(
        screen.getByTestId("experiment-probe-secondary"),
      ).toHaveTextContent("Secondary: probe not set");
    });
  });

  describe("renders Audience row as expected", () => {
    it("when all fields are set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-target")).toHaveTextContent(
        "Us Only",
      );
      expect(screen.getByTestId("experiment-channels")).toHaveTextContent(
        "Desktop Nightly, Desktop Beta,",
      );
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Firefox 80",
      );
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "40% of population",
      );
      expect(screen.getByTestId("experiment-total-enrolled")).toHaveTextContent(
        "totalling 68,000 expected enrolled clients",
      );
    });
    it("when no fields are set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        channels: [],
        firefoxMinVersion: null,
        populationPercent: 0,
        totalEnrolledClients: 0,
        proposedEnrollment: 0,
        proposedDuration: 0,
        targetingConfigSlug: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-target")).toHaveTextContent(
        "Target audience not set",
      );
      expect(screen.getByTestId("experiment-channels")).toHaveTextContent(
        "channel not set",
      );
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Firefox minimum version not set",
      );
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "Population percentage not set",
      );
      expect(screen.getByTestId("experiment-total-enrolled")).toHaveTextContent(
        "totalling expected enrolled clients not set",
      );
    });
  });

  describe("renders Duration row as expected", () => {
    it("when all fields are set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-duration")).toHaveTextContent(
        "28 days",
      );
      expect(screen.getByTestId("experiment-enrollment")).toHaveTextContent(
        "over an enrollment period of 1 day",
      );
    });
    it("when no fields are set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        proposedEnrollment: 0,
        proposedDuration: 0,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-duration")).toHaveTextContent(
        "Proposed duration not set",
      );
      expect(screen.getByTestId("experiment-enrollment")).toHaveTextContent(
        "over an enrollment period of proposed enrollment not set",
      );
    });
  });
});

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <MockedCache>
    <TableSummary {...{ experiment }} />
  </MockedCache>
);
