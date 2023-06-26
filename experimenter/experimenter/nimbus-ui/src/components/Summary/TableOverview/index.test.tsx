/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, within } from "@testing-library/react";
import React from "react";
import TableOverview from "src/components/Summary/TableOverview";
import { MockedCache, mockExperimentQuery, MOCK_CONFIG } from "src/lib/mocks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

describe("TableOverview", () => {
  it("renders rows displaying required fields at experiment creation as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject {...{ experiment }} />);

    expect(screen.getByTestId("experiment-slug")).toHaveTextContent(
      "demo-slug",
    );
    expect(screen.getByTestId("experiment-owner")).toHaveTextContent(
      "example@mozilla.com",
    );
    expect(screen.getByTestId("experiment-application")).toHaveTextContent(
      "Desktop",
    );
    expect(screen.getByTestId("experiment-hypothesis")).toHaveTextContent(
      "Realize material say pretty.",
    );
    expect(screen.getByTestId("experiment-team-projects")).toHaveTextContent(
      "Pocket",
    );
  });

  describe("renders 'Primary outcomes' row as expected", () => {
    it("with one outcome", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-outcome-primary"),
      ).toHaveTextContent("Picture-in-Picture");
    });
    it("with correct documentation URl", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        primaryOutcomes: ["picture_in_picture"],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("primary-outcome-picture_in_picture"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("primary-outcome-picture_in_picture"),
      ).toHaveAttribute(
        "href",
        "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/picture_in_picture",
      );
    });
    it("with multiple outcomes", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        primaryOutcomes: ["picture_in_picture", "feature_c"],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-outcome-primary"),
      ).toHaveTextContent("Picture-in-Picture, Feature C");
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        primaryOutcomes: [],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-outcome-primary"),
      ).not.toBeInTheDocument();
    });
  });

  describe("renders 'Secondary outcomes' row as expected", () => {
    it("with one outcome", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-outcome-secondary"),
      ).toHaveTextContent("Feature B");
    });
    it("with correct documentation URl", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        secondaryOutcomes: ["picture_in_picture"],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("secondary-outcome-picture_in_picture"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("secondary-outcome-picture_in_picture"),
      ).toHaveAttribute(
        "href",
        "https://mozilla.github.io/metric-hub/outcomes/firefox_desktop/picture_in_picture",
      );
    });
    it("with multiple outcomes", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        secondaryOutcomes: ["picture_in_picture", "feature_b"],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-outcome-secondary"),
      ).toHaveTextContent("Picture-in-Picture, Feature B");
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        secondaryOutcomes: [],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-outcome-secondary"),
      ).not.toBeInTheDocument();
    });

    describe("renders 'Public description' row as expected", () => {
      it("when set", () => {
        const { experiment } = mockExperimentQuery("demo-slug");
        render(<Subject {...{ experiment }} />);
        expect(screen.getByTestId("experiment-description")).toHaveTextContent(
          "Official approach present industry strategy dream piece.",
        );
      });
      it("when not set", () => {
        const { experiment } = mockExperimentQuery("demo-slug", {
          publicDescription: "",
        });
        render(<Subject {...{ experiment }} />);
        expect(screen.getByTestId("experiment-description")).toHaveTextContent(
          "Not set",
        );
      });
    });
  });

  describe("renders 'Feature config' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-feature-config")).toHaveTextContent(
        "Picture-in-Picture",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        featureConfigs: [],
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-feature-config")).toHaveTextContent(
        "Not set",
      );
    });
  });
  describe("renders 'Targeting config' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        targetingConfig: [MOCK_CONFIG.targetingConfigs![0]],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-targeting-config"),
      ).toHaveTextContent("Mac Only - Mac only configuration");
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        targetingConfig: [],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-targeting-config"),
      ).toHaveTextContent("Not set");
    });
  });

  describe("renders 'Team Projects' row as expected", () => {
    it("with one team project", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-team-projects")).toHaveTextContent(
        "Pocket",
      );
    });
    it("with multiple projects", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        projects: [
          { id: "1", name: "Pocket" },
          { id: "2", name: "VPN" },
        ],
      });
      render(<Subject {...{ experiment }} />);
      experiment.projects!.forEach((team) =>
        within(screen.getByTestId("experiment-team-projects")).findByText(
          team!.name!,
        ),
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        projects: [],
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-team-projects"),
      ).toHaveTextContent("Not set");
    });
  });
});

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <MockedCache>
    <TableOverview {...{ experiment }} />
  </MockedCache>
);
