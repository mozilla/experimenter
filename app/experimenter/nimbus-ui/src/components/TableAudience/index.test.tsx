/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import TableSummary from ".";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentChannel } from "../../types/globalTypes";

describe("TableAudience", () => {
  describe("renders 'Channels' row as expected", () => {
    it("with one channel", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        channels: [NimbusExperimentChannel.DESKTOP_BETA],
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-channels")).toHaveTextContent(
        "Desktop Beta",
      );
    });
    it("with multiple channels", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-channels")).toHaveTextContent(
        "Desktop Nightly, Desktop Beta",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        channels: [],
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-channels")).toHaveTextContent(
        "Not set",
      );
    });
  });
  describe("renders 'Minimum version' row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Firefox 80",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        firefoxMinVersion: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Not set",
      );
    });
  });

  describe("renders 'Population %' row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "40%",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        populationPercent: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "Not set",
      );
    });
  });

  describe("renders 'Expected enrolled clients' row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-total-enrolled")).toHaveTextContent(
        "68,000",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        totalEnrolledClients: 0,
      });
      render(<Subject experiment={data!} />);
      expect(
        screen.queryByTestId("experiment-total-enrolled"),
      ).not.toBeInTheDocument();
    });
  });

  describe("renders 'Custom audience' row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-target")).toHaveTextContent(
        "Us Only",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        targetingConfigSlug: null,
      });
      render(<Subject experiment={data!} />);
      expect(screen.queryByTestId("experiment-target")).not.toBeInTheDocument();
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
