/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, within } from "@testing-library/react";
import React from "react";
import { MOBILE_APPLICATIONS } from "src/components/PageEditAudience/FormAudience";
import TableAudience from "src/components/Summary/TableAudience";
import { MockedCache, mockExperimentQuery } from "src/lib/mocks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  NimbusExperimentApplicationEnum,
  NimbusExperimentChannelEnum,
} from "src/types/globalTypes";

describe("TableAudience", () => {
  describe("renders 'Channel' row as expected", () => {
    it("with one channel", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        channel: NimbusExperimentChannelEnum.BETA,
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

  describe("renders 'First Run Release Date' row for mobile", () => {
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter((application) =>
        MOBILE_APPLICATIONS.includes(application),
      ),
    )("with proposed release date", (application) => {
      const expectedDate = "2023-12-12";
      const { experiment } = mockExperimentQuery("demo-slug", {
        application,
        proposedReleaseDate: expectedDate,
        isFirstRun: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-release-date")).toHaveTextContent(
        expectedDate,
      );
    });
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter((application) =>
        MOBILE_APPLICATIONS.includes(application),
      ),
    )("when not set", (application) => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        application,
        isFirstRun: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-release-date")).toHaveTextContent(
        "Not set",
      );
    });
  });

  describe("render First Run fields based on application", () => {
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter(
        (application) => !MOBILE_APPLICATIONS.includes(application),
      ),
    )("when application is not mobile", (application) => {
      const { experiment } = mockExperimentQuery("demo-slug", { application });
      render(<Subject {...{ experiment }} />);
      expect(screen.queryByTestId("experiment-is-first-run")).toBeNull();
      expect(screen.queryByTestId("experiment-release-date")).toBeNull();
    });
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter((application) =>
        MOBILE_APPLICATIONS.includes(application),
      ),
    )("when application is mobile", (application) => {
      const expectedDate = "2023-12-12";
      const { experiment } = mockExperimentQuery("demo-slug", {
        application,
        proposedReleaseDate: expectedDate,
        isFirstRun: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-is-first-run")).toBeInTheDocument();
      expect(screen.getByTestId("experiment-release-date")).toBeInTheDocument();
    });
  });

  describe("renders 'First Run Experiment' row as expected", () => {
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter((application) =>
        MOBILE_APPLICATIONS.includes(application),
      ),
    )("with stick enrollment True", (application) => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        application,
        isFirstRun: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-is-first-run")).toHaveTextContent(
        "True",
      );
    });
    it.each(
      Object.values(NimbusExperimentApplicationEnum).filter((application) =>
        MOBILE_APPLICATIONS.includes(application),
      ),
    )("when not set", (application) => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        application,
        isFirstRun: false,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-is-first-run")).toHaveTextContent(
        "False",
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
        "40.0%",
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
      expect(screen.getByTestId("experiment-total-enrolled")).toHaveTextContent(
        "0",
      );
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

  it("Renders show button for recipe json", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject {...{ experiment }} />);
    expect(screen.queryByTestId("experiment-recipe-json")).toBeInTheDocument();
    expect(screen.queryByTestId("experiment-recipe-json")).toHaveTextContent(
      "{",
    );
    expect(screen.queryByText("Show More")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Show More"));
    expect(screen.queryByText("Hide")).toBeInTheDocument();
  });

  describe("renders 'Locales' row as expected", () => {
    it("when locales exist, displays them", () => {
      const data = {
        locales: [
          { name: "Quebecois", id: "1", code: "Qu" },
          { name: "Acholi", id: "2", code: "Ac" },
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

  describe("renders 'Locales' row as expected for old experiments", () => {
    it("when locales exist, displays them", () => {
      const data = {
        locales: [
          { name: "Quebecois", id: "1", code: "Qu" },
          { name: "Acholi", id: "2", code: "Ac" },
        ],
        application: NimbusExperimentApplicationEnum.FENIX,
      };
      const { experiment } = mockExperimentQuery("demo-slug", data);
      render(<Subject {...{ experiment }} />);
      data.locales.forEach((locale) =>
        within(screen.getByTestId("experiment-locales")).findByText(
          locale.name,
        ),
      );
    });
    it("when locales don't exist for old experiments, displays all", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        locales: [],
      });
      render(<Subject {...{ experiment }} />);
      await within(screen.getByTestId("experiment-locales")).findByText(
        "All locales",
      );
    });
  });

  describe("renders 'Languages' row as expected", () => {
    it("when languages exist, displays them", () => {
      const data = {
        languages: [
          { name: "English", id: "1", code: "En" },
          { name: "French", id: "2", code: "Fr" },
        ],
        application: NimbusExperimentApplicationEnum.FENIX,
      };
      const { experiment } = mockExperimentQuery("demo-slug", data);
      render(
        <Subject
          {...{
            experiment,
          }}
        />,
      );
      data.languages.forEach((language) =>
        within(screen.getByTestId("experiment-languages")).findByText(
          language.name,
        ),
      );
    });
    it("when languages don't exist, displays all", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        languages: [],
        application: NimbusExperimentApplicationEnum.FENIX,
      });
      render(
        <Subject
          {...{
            experiment,
          }}
        />,
      );
      await within(screen.getByTestId("experiment-languages")).findByText(
        "All Languages",
      );
    });
  });

  describe("renders 'Countries' row as expected", () => {
    it("when countries exist, displays them", async () => {
      const data = {
        countries: [
          { name: "Canada", id: "1", code: "Ca" },
          { name: "Germany", id: "2", code: "Ge" },
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

  describe("renders 'Stick Enrollment' row as expected", () => {
    it("with stick enrollment True", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        isSticky: true,
      });
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-is-sticky")).toHaveTextContent(
        "True",
      );
    });
    it("when not set", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {});
      render(<Subject {...{ experiment }} />);
      expect(screen.getByTestId("experiment-is-sticky")).toHaveTextContent(
        "False",
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
    <TableAudience {...{ experiment }} />
  </MockedCache>
);
