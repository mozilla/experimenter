/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import DirectoryTable, {
  DirectoryColumnTitle,
  DirectoryColumnOwner,
  DirectoryColumnFeature,
  DirectoryLiveTable,
  DirectoryCompleteTable,
  DirectoryDraftsTable,
} from ".";
import { mockSingleDirectoryExperiment } from "../../../lib/mocks";
import {
  getProposedEndDate,
  getProposedEnrollmentRange,
  humanDate,
} from "../../../lib/dateUtils";

const experiment = mockSingleDirectoryExperiment();

const TestTable = ({ children }: { children: React.ReactNode }) => (
  <table>
    <tbody>
      <tr>{children}</tr>
    </tbody>
  </table>
);

describe("DirectoryColumnTitle", () => {
  it("renders the experiment name and slug", () => {
    render(
      <TestTable>
        <DirectoryColumnTitle {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-title-name")).toHaveTextContent(
      experiment.name,
    );
    expect(screen.getByTestId("directory-title-slug")).toHaveTextContent(
      experiment.slug,
    );
  });
});

describe("DirectoryColumnOwner", () => {
  it("renders the experiment owner if present", () => {
    render(
      <TestTable>
        <DirectoryColumnOwner {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      experiment.owner!.username,
    );
  });

  it("renders the NotSet label if owner is not present", () => {
    render(
      <TestTable>
        {/**
         * Intentionally disable ts check because we can still possibly
         * have no owner on older experiments that didn't assign one
         * @ts-ignore */}
        <DirectoryColumnOwner {...experiment} owner={null} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Not set",
    );
  });
});

describe("DirectoryColumnFeature", () => {
  it("renders the feature config if present", () => {
    render(
      <TestTable>
        <DirectoryColumnFeature {...experiment} />
      </TestTable>,
    );
    expect(
      screen.getByTestId("directory-feature-config-name"),
    ).toHaveTextContent(experiment.featureConfig!.name);
    expect(
      screen.getByTestId("directory-feature-config-slug"),
    ).toHaveTextContent(experiment.featureConfig!.slug);
  });

  it("renders the None label if feature config is not present", () => {
    render(
      <TestTable>
        <DirectoryColumnFeature {...experiment} featureConfig={null} />
      </TestTable>,
    );
    expect(
      screen.getByTestId("directory-feature-config-none"),
    ).toBeInTheDocument();
  });
});

function expectTableCells(testId: string, cellTexts: string[]) {
  const cells = screen.getAllByTestId(testId);
  expect(cells).toHaveLength(cellTexts.length);
  cellTexts.forEach((text, index) => {
    expect(cells[index].textContent).toEqual(expect.stringContaining(text));
  });
}

describe("DirectoryTable", () => {
  it("renders as expected with default columns", () => {
    const experiments = [experiment];
    render(<DirectoryTable title="Woozle Wuzzle" {...{ experiments }} />);
    expectTableCells("directory-table-header", [
      "Woozle Wuzzle",
      "Owner",
      "Feature",
    ]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
    ]);
    expect(screen.getAllByTestId("directory-table-row")).toHaveLength(
      experiments.length,
    );
  });

  it("renders as expected without experiments", () => {
    render(<DirectoryTable title="Sweet Pea" experiments={[]} />);
    expectTableCells("directory-table-header", ["Sweet Pea"]);
    expect(
      screen.getByTestId("directory-table-no-experiments"),
    ).toBeInTheDocument();
  });

  it("renders as expected with custom columns", () => {
    render(
      <DirectoryTable
        title="Record Numbers"
        experiments={[experiment]}
        columns={[
          { label: "Cant think", component: DirectoryColumnTitle },
          {
            label: "Of a title",
            component: ({ status }) => (
              <td data-testid="directory-table-cell">{status}</td>
            ),
          },
        ]}
      />,
    );
    expectTableCells("directory-table-header", ["Cant think", "Of a title"]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.status!,
    ]);
  });
});

describe("DirectoryLiveTable", () => {
  it("renders as expected with custom columns", () => {
    render(
      <DirectoryLiveTable
        title="Live Experiments"
        experiments={[experiment]}
      />,
    );
    expectTableCells("directory-table-header", [
      "Live Experiments",
      "Owner",
      "Feature",
      "Enrolling",
      "Ending",
      "Monitoring",
    ]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
      getProposedEnrollmentRange(experiment) as string,
      getProposedEndDate(experiment) as string,
      "Grafana",
    ]);
  });
});

describe("DirectoryCompleteTable", () => {
  it("renders as expected with custom columns", () => {
    render(
      <DirectoryCompleteTable title="Completed" experiments={[experiment]} />,
    );
    expectTableCells("directory-table-header", [
      "Completed",
      "Owner",
      "Feature",
      "Started",
      "Ended",
      "Results",
    ]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
      humanDate(experiment.startDate!),
      humanDate(experiment.endDate!),
      "Results",
    ]);
  });
});

describe("DirectoryDraftsTable", () => {
  it("renders as expected with custom columns", () => {
    render(<DirectoryDraftsTable title="Drafts" experiments={[experiment]} />);
    expectTableCells("directory-table-header", ["Drafts", "Owner", "Feature"]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
    ]);
  });
});
