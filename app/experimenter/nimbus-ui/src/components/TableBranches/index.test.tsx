/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { Subject, MOCK_EXPERIMENT } from "./mocks";

describe("TableBranches", () => {
  it("renders as expected with defaults", () => {
    render(<Subject />);
    expect(screen.queryByTestId("not-set")).not.toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
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
    expect(screen.getByTestId("not-set")).toBeInTheDocument();
  });

  it("hides feature value when feature schema is null", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          featureConfig: {
            ...MOCK_EXPERIMENT.featureConfig!,
            schema: null,
          },
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
              __typename: "NimbusBranchType",
              ...expected,
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

  it("displays not set for missing branch properties", () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          treatmentBranches: [
            {
              __typename: "NimbusBranchType",
              name: "",
              slug: "",
              description: "",
              ratio: 0,
              featureValue: null,
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
    for (const name of [
      "name",
      "slug",
      "description",
      "ratio",
      "featureValue",
    ] as const) {
      const cell = subjectTable.querySelector(`[data-testid='branch-${name}']`);
      expect(cell).toBeInTheDocument();
      const notSet = cell!.querySelector("[data-testid='not-set']");
      expect(notSet).toBeInTheDocument();
    }
  });
});
