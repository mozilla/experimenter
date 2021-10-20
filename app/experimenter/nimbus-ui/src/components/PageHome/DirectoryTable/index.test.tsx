/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent } from "@testing-library/dom";
import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import DirectoryTable, {
  Column,
  ColumnComponent,
  ColumnSortOrder,
  DirectoryColumnFeature,
  DirectoryColumnOwner,
  DirectoryColumnTitle,
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
  SortableColumnTitle,
} from ".";
import { UpdateSearchParams } from "../../../hooks/useSearchParamsState";
import { getProposedEnrollmentRange, humanDate } from "../../../lib/dateUtils";
import {
  mockDirectoryExperiments,
  mockSingleDirectoryExperiment,
} from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { getAllExperiments_experiments } from "../../../types/getAllExperiments";

const experiment = mockSingleDirectoryExperiment();

const TestTable = ({ children }: { children: React.ReactNode }) => {
  return (
    <RouterSlugProvider>
      <table>
        <tbody>
          <tr>{children}</tr>
        </tbody>
      </table>
    </RouterSlugProvider>
  );
};

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
    render(
      <RouterSlugProvider>
        <DirectoryTable {...{ experiments }} />
      </RouterSlugProvider>,
    );
    expectTableCells("directory-table-header", ["Name", "Owner", "Feature"]);
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
    render(
      <RouterSlugProvider>
        <DirectoryTable experiments={[]} />
      </RouterSlugProvider>,
    );
    expect(screen.getByTestId("no-experiments")).toBeInTheDocument();
  });

  it("renders as expected with custom columns", () => {
    render(
      <RouterSlugProvider>
        <DirectoryTable
          experiments={[experiment]}
          columns={[
            {
              label: "Cant think",
              sortBy: "name",
              component: DirectoryColumnTitle,
            },
            {
              label: "Of a title",
              sortBy: "status",
              component: ({ status }) => (
                <td data-testid="directory-table-cell">{status}</td>
              ),
            },
          ]}
        />
      </RouterSlugProvider>,
    );
    expectTableCells("directory-table-header", ["Cant think", "Of a title"]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.status!,
    ]);
  });

  // TODO: not exhaustively testing all sort orders here, might be worth adding more?
  // Sorting is more fully covered in lib/experiment.test.ts
  it("supports sorting by name", async () => {
    const experiments = mockDirectoryExperiments();
    const experimentNames = experiments.map((experiment) => experiment.name);
    const getExperimentNamesFromTable = () =>
      screen.getAllByTestId("directory-title-name").map((el) => el.textContent);

    render(
      <RouterSlugProvider>
        <DirectoryTable {...{ experiments }} />
      </RouterSlugProvider>,
    );

    expect(getExperimentNamesFromTable()).toEqual(experimentNames);

    const nameSortButton = screen
      .getAllByTestId("sort-select")
      .find((el) => el.title === "Name")!;
    expect(nameSortButton).toBeDefined();

    fireEvent.click(nameSortButton);
    await waitFor(() =>
      expect(getExperimentNamesFromTable()).toEqual(
        [...experimentNames].sort((a, b) => a.localeCompare(b)),
      ),
    );

    fireEvent.click(nameSortButton);
    await waitFor(() =>
      expect(getExperimentNamesFromTable()).toEqual(
        [...experimentNames].sort((a, b) => b.localeCompare(a)),
      ),
    );

    fireEvent.click(nameSortButton);
    await waitFor(() =>
      expect(getExperimentNamesFromTable()).toEqual(experimentNames),
    );
  });
});

describe("DirectoryLiveTable", () => {
  it.each([
    ["looker link is present", experiment, "Looker"],
    [
      "results are ready",
      { ...experiment, resultsReady: true, monitoringDashboardUrl: null },
      "Results",
    ],
    [
      "neither is present",
      { ...experiment, monitoringDashboardUrl: null },
      "N/A",
    ],
    [
      "both are present",
      { ...experiment, resultsReady: true },
      "LookerOpens in new windowResults",
    ],
  ])(
    "renders as expected with custom columns when %s",
    (_, experiment: getAllExperiments_experiments, expectedResult: string) => {
      render(
        <RouterSlugProvider>
          <DirectoryLiveTable experiments={[experiment]} />
        </RouterSlugProvider>,
      );
      expectTableCells("directory-table-header", [
        "Name",
        "Owner",
        "Feature",
        "Started",
        "Enrolling",
        "Ending",
        "Results",
      ]);
      expectTableCells("directory-table-cell", [
        experiment.name,
        experiment.owner!.username,
        experiment.featureConfig!.name,
        humanDate(experiment.startDate!),
        getProposedEnrollmentRange(experiment) as string,
        humanDate(experiment.computedEndDate!),
        expectedResult,
      ]);
    },
  );
});

describe("DirectoryCompleteTable", () => {
  it("renders as expected with custom columns", () => {
    render(
      <RouterSlugProvider>
        <DirectoryCompleteTable experiments={[experiment]} />
      </RouterSlugProvider>,
    );
    expectTableCells("directory-table-header", [
      "Name",
      "Owner",
      "Feature",
      "Started",
      "Ended",
      "Results",
    ]);
    const header = screen
      .getAllByTestId("directory-table-header")
      .find((el) => el.textContent === "Results");
    expect(header!.tagName).not.toEqual("BUTTON");
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
      humanDate(experiment.startDate!),
      humanDate(experiment.computedEndDate!),
      "Results",
    ]);
  });
});

describe("DirectoryDraftsTable", () => {
  it("renders as expected with custom columns", () => {
    render(
      <RouterSlugProvider>
        <DirectoryDraftsTable experiments={[experiment]} />
      </RouterSlugProvider>,
    );
    expectTableCells("directory-table-header", ["Name", "Owner", "Feature"]);
    expectTableCells("directory-table-cell", [
      experiment.name,
      experiment.owner!.username,
      experiment.featureConfig!.name,
    ]);
  });
});

describe("SortableColumnTitle", () => {
  const columnComponent: ColumnComponent = ({ name }) => (
    <td data-testid="directory-table-cell">{name}</td>
  );

  const column: Column = {
    label: "Name",
    sortBy: "name",
    component: columnComponent,
  };

  let nextParams: URLSearchParams, updateSearchParams: UpdateSearchParams;

  beforeEach(() => {
    nextParams = new URLSearchParams();
    updateSearchParams = jest.fn((updaterFn) => updaterFn(nextParams));
  });

  const Subject = (props: { columnSortOrder: ColumnSortOrder }) => (
    <TestTable>
      <SortableColumnTitle {...{ ...props, column, updateSearchParams }} />
    </TestTable>
  );

  const expectClass = (element: HTMLElement, cls: string, toHave = true) => {
    const matcher = toHave ? expect(element) : expect(element).not;
    matcher.toHaveClass(cls);
  };

  const commonTestCase =
    (
      initiallySelected = false,
      initiallyDescending = false,
      paramsWillHaveSelected = true,
      paramsWillHaveDescending = false,
    ) =>
    () => {
      render(
        <Subject
          columnSortOrder={{
            column: initiallySelected ? column : undefined,
            descending: initiallyDescending,
          }}
        />,
      );

      const header = screen.getByTestId("directory-table-header");
      expectClass(header, "sort-selected", initiallySelected);
      expectClass(header, "sort-descending", initiallyDescending);

      const button = screen.getByTestId("sort-select");
      expect(button).toHaveTextContent(column.label);

      fireEvent.click(button);
      expect(updateSearchParams).toHaveBeenCalled();

      if (paramsWillHaveSelected) {
        expect(nextParams.get("sortByLabel")).toEqual(column.label);
      } else {
        expect(nextParams.has("sortByLabel")).toBeFalsy();
      }
      expect(nextParams.has("descending"))[
        paramsWillHaveDescending ? "toBeTruthy" : "toBeFalsy"
      ]();
    };

  it(
    "renders default as expected and supports ascending sort selection",
    commonTestCase(false, false, true, false),
  );

  it(
    "renders ascending sort as expected and support descending sort selection",
    commonTestCase(true, false, true, true),
  );

  it(
    "renders descending sort as expected and support sort reset",
    commonTestCase(true, true, false, false),
  );
});
