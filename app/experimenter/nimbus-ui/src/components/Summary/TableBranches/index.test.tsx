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
import { NO_BRANCHES_COPY } from ".";
import { getExperiment_experimentBySlug_treatmentBranches_screenshots } from "../../../types/getExperiment";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

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
              featureValue: null,
              featureEnabled: false,
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

  it("hides feature value when feature is not enabled", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          referenceBranch: {
            ...MOCK_EXPERIMENT.referenceBranch!,
            featureEnabled: false,
          },
          treatmentBranches: [
            {
              ...MOCK_EXPERIMENT.treatmentBranches![0]!,
              featureEnabled: false,
            },
          ],
        }}
      />,
    );
    expect(screen.queryByTestId("branch-value")).not.toBeInTheDocument();
    for (const cell of screen.queryAllByTestId("branch-enabled")) {
      expect(cell).toHaveTextContent("False");
    }
  });

  it("renders expected content", () => {
    const expected = {
      name: "expected name",
      slug: "expected slug",
      description: "expected description",
      ratio: 42,
      featureValue: '{ "thing": true }',
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
              featureEnabled: true,
            },
            ...MOCK_EXPERIMENT.treatmentBranches!,
          ],
        }}
      />,
    );

    const branchTables = screen.queryAllByTestId("table-branch");
    expect(branchTables).toHaveLength(3);

    const subjectTable = branchTables[1];

    const cell = subjectTable.querySelector(`[data-testid='branch-enabled']`);
    expect(cell).toBeInTheDocument();
    expect(cell).toHaveTextContent("True");

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
              featureValue: '{ "thing": true }',
              featureEnabled: true,
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
      featureValue: '{ "thing": true }',
      screenshots: [],
    };

    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              ...expected,
              featureEnabled: true,
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
      featureValue: '{ "thing": true }',
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
              featureEnabled: true,
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
      featureValue: '{ "thing": true }',
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
              featureEnabled: true,
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
              featureValue: null,
              featureEnabled: true,
              screenshots: [],
            },
            {
              id: null,
              name: "",
              slug: "",
              description: "",
              ratio: 0,
              featureValue: null,
              featureEnabled: true,
              screenshots: [],
            },
          ],
        }}
      />,
    );

    const branchTables = screen.queryAllByTestId("table-branch");
    expect(branchTables).toHaveLength(2);

    const subjectTable = branchTables[1];
    for (const property of ["description", "ratio", "featureValue"] as const) {
      const cell = subjectTable.querySelector(
        `[data-testid='branch-${property}']`,
      );
      expect(cell).toBeInTheDocument();
      const notSet = cell!.querySelector("[data-testid='not-set']");
      expect(notSet).toBeInTheDocument();
    }
  });
});
