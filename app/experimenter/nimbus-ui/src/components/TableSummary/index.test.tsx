/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { MockedCache, mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import TableSummary from ".";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

describe("TableSummary", () => {
  it("renders rows displaying required fields at experiment creation as expected", () => {
    const { data } = mockExperimentQuery("demo-slug");
    render(<Subject experiment={data!} />);

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

  describe("renders 'Primary probe sets' row as expected", () => {
    it("with one probe set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-probe-primary")).toHaveTextContent(
        "Picture-in-Picture",
      );
    });
    it("with multiple probe sets", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        primaryProbeSets: [
          {
            __typename: "NimbusProbeSetType",
            id: "1",
            slug: "picture_in_picture",
            name: "Picture-in-Picture",
          },
          {
            __typename: "NimbusProbeSetType",
            id: "2",
            slug: "feature_c",
            name: "Feature C",
          },
        ],
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-probe-primary")).toHaveTextContent(
        "Picture-in-Picture, Feature C",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        primaryProbeSets: [],
      });
      render(<Subject experiment={data!} />);
      expect(
        screen.queryByTestId("experiment-probe-primary"),
      ).not.toBeInTheDocument();
    });
  });

  describe("renders 'Secondary probe sets' row as expected", () => {
    it("with one probe set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(
        screen.getByTestId("experiment-probe-secondary"),
      ).toHaveTextContent("Feature B");
    });
    it("with multiple probe sets", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        secondaryProbeSets: [
          {
            __typename: "NimbusProbeSetType",
            id: "1",
            slug: "picture_in_picture",
            name: "Picture-in-Picture",
          },
          {
            __typename: "NimbusProbeSetType",
            id: "2",
            slug: "feature_b",
            name: "Feature B",
          },
        ],
      });
      render(<Subject experiment={data!} />);
      expect(
        screen.getByTestId("experiment-probe-secondary"),
      ).toHaveTextContent("Picture-in-Picture, Feature B");
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        secondaryProbeSets: [],
      });
      render(<Subject experiment={data!} />);
      expect(
        screen.queryByTestId("experiment-probe-secondary"),
      ).not.toBeInTheDocument();
    });

    describe("renders 'Public description' row as expected", () => {
      it("when set", () => {
        const { data } = mockExperimentQuery("demo-slug");
        render(<Subject experiment={data!} />);
        expect(screen.getByTestId("experiment-description")).toHaveTextContent(
          "Official approach present industry strategy dream piece.",
        );
      });
      it("when not set", () => {
        const { data } = mockExperimentQuery("demo-slug", {
          publicDescription: null,
        });
        render(<Subject experiment={data!} />);
        expect(screen.getByTestId("experiment-description")).toHaveTextContent(
          "Not set",
        );
      });
    });
  });

  describe("renders 'Feature config' row as expected", () => {
    it("when set", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        featureConfig: MOCK_CONFIG.featureConfig![1],
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("experiment-feature-config")).toHaveTextContent(
        "Mauris odio erat",
      );
    });
    it("when not set", () => {
      const { data } = mockExperimentQuery("demo-slug");
      render(<Subject experiment={data!} />);
      expect(
        screen.queryByTestId("experiment-feature-config"),
      ).not.toBeInTheDocument();
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
