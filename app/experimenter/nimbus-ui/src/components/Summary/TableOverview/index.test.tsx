/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableOverview from ".";
import { RISK_QUESTIONS } from "../../../lib/constants";
import {
  MockedCache,
  mockExperimentQuery,
  MOCK_CONFIG,
} from "../../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";

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
  });

  describe("renders 'Primary outcomes' row as expected", () => {
    it("with one outcome", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-outcome-primary"),
      ).toHaveTextContent("Picture-in-Picture");
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

  describe("renders 'Risk mitigation question' rows as expected", () => {
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: null,
        riskBrand: null,
        riskPartnerRelated: null,
      });
      render(<Subject {...{ experiment }} />);
      for (const question of Object.values(RISK_QUESTIONS)) {
        expect(screen.getByText(question, { exact: false })).toHaveTextContent(
          "Not set",
        );
      }
    });
    it("when set to false", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: false,
        riskBrand: false,
        riskPartnerRelated: false,
      });
      render(<Subject {...{ experiment }} />);
      for (const question of Object.values(RISK_QUESTIONS)) {
        expect(screen.getByText(question, { exact: false })).toHaveTextContent(
          "No",
        );
      }
    });
    it("when set to true", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: true,
        riskBrand: true,
        riskPartnerRelated: true,
      });
      render(<Subject {...{ experiment }} />);
      for (const question of Object.values(RISK_QUESTIONS)) {
        expect(screen.getByText(question, { exact: false })).toHaveTextContent(
          "Yes",
        );
      }
    });
  });

  describe("renders 'Feature config' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-feature-config")).toHaveTextContent(
        "Mauris odio erat",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
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
