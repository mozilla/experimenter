/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableRiskMitigation from "src/components/Summary/TableRiskMitigation";
import { MockedCache, mockExperimentQuery } from "src/lib/mocks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

describe("TableRiskMitigation", () => {
  describe("renders 'Risk mitigation question' rows as expected", () => {
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: null,
        riskBrand: null,
        riskPartnerRelated: null,
      });
      render(<Subject {...{ experiment }} />);

      expect(
        screen.getByTestId("experiment-risk-mitigation-question-1"),
      ).toHaveTextContent("Not set");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-2"),
      ).toHaveTextContent("Not set");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-3"),
      ).toHaveTextContent("Not set");
    });
    it("when set to false", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: false,
        riskBrand: false,
        riskPartnerRelated: false,
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-1"),
      ).toHaveTextContent("No");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-2"),
      ).toHaveTextContent("No");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-3"),
      ).toHaveTextContent("No");
    });
    it("when set to true", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        riskRevenue: true,
        riskBrand: true,
        riskPartnerRelated: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-1"),
      ).toHaveTextContent("Yes");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-2"),
      ).toHaveTextContent("Yes");
      expect(
        screen.getByTestId("experiment-risk-mitigation-question-3"),
      ).toHaveTextContent("Yes");
    });
  });
});

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <MockedCache>
    <TableRiskMitigation {...{ experiment }} />
  </MockedCache>
);
