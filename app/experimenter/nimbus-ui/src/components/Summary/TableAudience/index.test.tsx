/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, within } from "@testing-library/react";
import React from "react";
import TableAudience from ".";
import { MockedCache, mockExperimentQuery } from "../../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { NimbusExperimentChannel } from "../../../types/globalTypes";

describe("TableAudience", () => {
  describe("renders 'Channel' row as expected", () => {
    it("with one channel", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        channel: NimbusExperimentChannel.BETA,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-channel")).toHaveTextContent(
        "Desktop Beta",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        channel: null,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-channel")).toHaveTextContent(
        "Not set",
      );
    });
  });
  describe("renders 'Minimum version' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Firefox 16",
      );
      expect(screen.getByTestId("experiment-ff-max")).toHaveTextContent(
        "Firefox 64",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        firefoxMinVersion: null,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-ff-min")).toHaveTextContent(
        "Not set",
      );
    });
  });

  describe("renders 'Population %' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "40%",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        populationPercent: null,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-population")).toHaveTextContent(
        "Not set",
      );
    });
  });

  describe("renders 'Expected enrolled clients' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-total-enrolled")).toHaveTextContent(
        "68,000",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        totalEnrolledClients: 0,
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-total-enrolled"),
      ).not.toBeInTheDocument();
    });
  });

  describe("renders 'Advanced Targeting' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-target")).toHaveTextContent(
        "Mac Only",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        targetingConfigSlug: null,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.queryByTestId("experiment-target")).not.toBeInTheDocument();
    });
    it("when set with deprecated value", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        targetingConfigSlug: "deprecated_slug",
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-target")).toHaveTextContent(
        "Deprecated: deprecated_slug",
      );
    });
  });

  describe("renders 'Full targeting expression' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(
        screen.getByTestId("experiment-target-expression"),
      ).toHaveTextContent(experiment.jexlTargetingExpression!);
    });
    it("when jexlTargetingExpression is empty", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        jexlTargetingExpression: "",
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-target-expression"),
      ).not.toBeInTheDocument();
    });
  });

  describe("renders 'Recipe JSON' row as expected", () => {
    it("when set", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-recipe-json")).toBeInTheDocument();
    });
    it("when recipeJson is null", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        recipeJson: null,
      });
      render(<Subject {...{ experiment }} />);
      expect(
        screen.queryByTestId("experiment-recipe-json"),
      ).not.toBeInTheDocument();
    });
  });

  it("hides details when withFullDetails = false", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject {...{ experiment, withFullDetails: false }} />);
    expect(
      screen.queryByTestId("experiment-recipe-json"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("experiment-target-expression"),
    ).not.toBeInTheDocument();
  });

  describe("renders 'Locales' row as expected", () => {
    it("when locales exist, displays them", () => {
      const data = {
        locales: [
          { name: "Quebecois", id: 1 },
          { name: "Acholi", id: 2 },
        ],
      };
      const { experiment } = mockExperimentQuery("demo-slug", data);
      render(<Subject {...{ experiment }} />);
      data.locales.forEach((locale) =>
        within(screen.getByTestId("experiment-locales")).findByText(
          locale.name,
        ),
      );
    });
    it("when locales don't exist, displays all", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        locales: [],
      });
      render(<Subject {...{ experiment }} />);
      await within(screen.getByTestId("experiment-locales")).findByText(
        "All locales",
      );
    });
  });

  describe("renders 'Countries' row as expected", () => {
    it("when countries exist, displays them", async () => {
      const data = {
        countries: [
          { name: "Canada", id: 1 },
          { name: "Germany", id: 2 },
        ],
      };
      const { experiment } = mockExperimentQuery("demo-slug", data);
      render(<Subject {...{ experiment }} />);
      data.countries.forEach((country) =>
        within(screen.getByTestId("experiment-countries")).findByText(
          country.name,
        ),
      );
    });
    it("when countries don't exist, displays all", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        countries: [],
      });
      render(<Subject {...{ experiment }} />);
      await within(screen.getByTestId("experiment-countries")).findByText(
        "All countries",
      );
    });
  });
});

const Subject = ({
  experiment,
  withFullDetails = true,
}: {
  experiment: getExperiment_experimentBySlug;
  withFullDetails?: boolean;
}) => (
  <MockedCache>
    <TableAudience {...{ experiment, withFullDetails }} />
  </MockedCache>
);
