/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import { NO_BRANCHES_COPY } from "src/components/Summary/TableBranches";
import {
  MOCK_EXPERIMENT,
  Subject,
} from "src/components/Summary/TableBranches/mocks";
import { mockExperimentQuery } from "src/lib/mocks";
import { getExperiment_experimentBySlug_treatmentBranches_screenshots } from "src/types/getExperiment";

describe("TableBranches", () => {
  it("renders as expected with defaults", () => {
    render(<Subject />);
    expect(screen.queryByTestId("not-set")).not.toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches (2)",
    );
  });

  it("handles zero defined branches", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          referenceBranch: null,
          treatmentBranches: null,
        }}
      />,
    );
    expect(screen.getByTestId("not-set")).toHaveTextContent(NO_BRANCHES_COPY);
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(0);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches",
    );
  });

  it("displays expected text with no branch names set", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          referenceBranch: {
            ...MOCK_EXPERIMENT.referenceBranch!,
            slug: "",
          },
          treatmentBranches: [
            {
              id: null,
              name: "",
              slug: "",
              description: "",
              ratio: 0,
              featureValues: [],
              screenshots: [],
            },
          ],
        }}
      />,
    );
    expect(screen.getByTestId("not-set")).toHaveTextContent(NO_BRANCHES_COPY);
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(0);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches",
    );
  });

  it("hides feature value when feature schema is null", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          featureConfigs: MOCK_EXPERIMENT.featureConfigs!.map((f) => ({
            ...f!,
            schema: null,
          })),
        }}
      />,
    );
    expect(screen.queryByTestId("branch-value")).not.toBeInTheDocument();
  });

  it("renders expected content", () => {
    const featureValue = '{ "thing": true }';
    const expected = {
      name: "expected name",
      slug: "expected slug",
      description: "expected description",
      ratio: 42,
      featureValue,
    };

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              ...expected,
              id: 456,
              screenshots: [],
              featureValues: [
                { featureConfig: { id: 1 }, value: featureValue },
              ],
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const branchTables = screen.queryAllByTestId("table-branch");
    expect(branchTables).toHaveLength(3);

    const subjectTable = branchTables[1];

    for (const [name, value] of Object.entries(expected)) {
      const cell = subjectTable.querySelector(`[data-testid='branch-${name}']`);
      expect(cell).toBeInTheDocument();
      expect(cell).toHaveTextContent(String(value));
    }
  });

  it("renders screenshots when present", () => {
    const expectedScreenshots: getExperiment_experimentBySlug_treatmentBranches_screenshots[] =
      [
        {
          id: 123,
          description: "first",
          image: "https://example.com/image1",
        },
        {
          id: 456,
          description: "second",
          image: "https://example.com/image2",
        },
        {
          id: 789,
          description: "third",
          image: "https://example.com/image3",
        },
      ];

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              id: 456,
              name: "expected name",
              slug: "expected slug",
              description: "expected description",
              ratio: 42,
              featureValues: [
                { featureConfig: { id: 1 }, value: '{ "thing": true }' },
              ],
              screenshots: expectedScreenshots,
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const branchTables = screen.queryAllByTestId("table-branch");
    expect(branchTables).toHaveLength(3);

    const subjectTable = branchTables[1];
    const screenshotsRow = subjectTable.querySelector(
      "[data-testid='branch-screenshots']",
    );
    expect(screenshotsRow).not.toBeNull();
    const screenshotFigures = screenshotsRow!.querySelectorAll(
      "[data-testid='branch-screenshot']",
    );
    expect(screenshotFigures).toHaveLength(expectedScreenshots.length);
    screenshotFigures.forEach((figure, idx) => {
      const expectedScreenshot = expectedScreenshots[idx];
      expect(figure.querySelector("figcaption")).toHaveTextContent(
        expectedScreenshot.description!,
      );
      expect(figure.querySelector("img")).toHaveAttribute(
        "src",
        expectedScreenshot.image,
      );
    });
  });

  it("supports promote to rollout buttons to clone the experiment", async () => {
    const expected = {
      id: 456,
      name: "expected name",
      slug: "expected-slug",
      description: "expected description",
      ratio: 42,
      featureValues: [{ featureConfig: { id: 1 }, value: '{ "thing": true }' }],
      screenshots: [],
    };

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              ...expected,
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const promoteButtons = screen.queryAllByTestId("promote-rollout");
    expect(promoteButtons).toHaveLength(3);

    const subjectButton = promoteButtons[1];
    act(() => void fireEvent.click(subjectButton));

    await waitFor(() => {
      const dialog = screen.queryByTestId("CloneDialog");
      expect(dialog).toBeInTheDocument();
      expect(dialog!).toHaveAttribute("data-rolloutbranchslug", expected.slug);
    });
  });

  it("shows promote to rollout buttons for non-rollout experiments", async () => {
    const expected = {
      id: 456,
      name: "expected name",
      slug: "expected-slug",
      description: "expected description",
      ratio: 42,
      featureValues: [{ featureConfig: { id: 1 }, value: '{ "thing": true }' }],
      screenshots: [],
    };

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          isRollout: false,
          treatmentBranches: [
            {
              ...expected,
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const promoteButtons = screen.queryAllByTestId("promote-rollout");
    expect(promoteButtons).toHaveLength(3);
  });

  it("hides promote to rollout buttons for rollouts", async () => {
    const expected = {
      id: 456,
      name: "expected name",
      slug: "expected-slug",
      description: "expected description",
      ratio: 42,
      featureValues: [{ featureConfig: { id: 1 }, value: '{ "thing": true }' }],
      screenshots: [],
    };

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          isRollout: true,
          treatmentBranches: [
            {
              ...expected,
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const promoteButtons = screen.queryAllByTestId("promote-rollout");
    expect(promoteButtons).toHaveLength(0);
  });

  it("hides branches without 'slug' set, displays not set for missing branch properties", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              id: 456,
              name: "treatment",
              slug: "treatment-1",
              description: "",
              ratio: 0,
              featureValues: [],
              screenshots: [],
            },
            {
              id: null,
              name: "",
              slug: "",
              description: "",
              ratio: 0,
              featureValues: [],
              screenshots: [],
            },
          ],
        }}
      />,
    );

    const branchTables = screen.queryAllByTestId("table-branch");
    expect(branchTables).toHaveLength(2);

    const subjectTable = branchTables[1];
    for (const property of ["description", "ratio"] as const) {
      const cell = subjectTable.querySelector(
        `[data-testid='branch-${property}']`,
      );
      expect(cell).toBeInTheDocument();
      const notSet = cell!.querySelector("[data-testid='not-set']");
      expect(notSet).toBeInTheDocument();
    }
  });
});

describe("renders localization row as expected", () => {
  it("when set", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      isLocalized: true,
      localizations: "test",
    });
    render(<Subject {...{ experiment }} />);
    expect(screen.getByTestId("experiment-localizations")).toHaveTextContent(
      "test",
    );
  });

  it("when isLocalized is not checked and localized content is set", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      isLocalized: false,
      localizations: "test",
    });
    render(<Subject {...{ experiment }} />);
    expect(screen.queryByTestId("experiment-localizations")).toBeNull();
  });

  it("renders show button for localized content", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      isLocalized: true,
      localizations: "test",
    });
    render(<Subject {...{ experiment }} />);
    const localizations = screen.getByTestId("experiment-localizations");
    expect(localizations).toHaveTextContent("test");
    const showMore = screen.getByTestId("experiment-localizations-show-more");
    fireEvent.click(showMore);
    screen.getByTestId("experiment-localizations-hide");
  });
});
