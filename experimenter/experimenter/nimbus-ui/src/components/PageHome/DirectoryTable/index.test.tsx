/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import DirectoryTable, {
  Column,
  ColumnComponent,
  ColumnSortOrder,
  DirectoryColumnApplication,
  DirectoryColumnChannel,
  DirectoryColumnEndDate,
  DirectoryColumnEnrollmentDate,
  DirectoryColumnFeature,
  DirectoryColumnFirefoxMaxVersion,
  DirectoryColumnFirefoxMinVersion,
  DirectoryColumnOwner,
  DirectoryColumnPopulationPercent,
  DirectoryColumnQA,
  DirectoryColumnStartDate,
  DirectoryColumnTitle,
  DirectoryColumnUnpublishedUpdates,
  SortableColumnTitle,
} from "src/components/PageHome/DirectoryTable";
import { UpdateSearchParams } from "src/hooks/useSearchParamsState";
import { QA_STATUS_PROPERTIES } from "src/lib/constants";
import { getProposedEnrollmentRange, humanDate } from "src/lib/dateUtils";
import {
  mockDirectoryExperiments,
  mockSingleDirectoryExperiment,
} from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

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
  it("renders the experiment name", () => {
    render(
      <TestTable>
        <DirectoryColumnTitle {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-title-name")).toHaveTextContent(
      experiment.name,
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

describe("DirectoryColumnQA", () => {
  it("renders the QA status field if present", () => {
    render(
      <TestTable>
        <DirectoryColumnQA {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell-qa")).toHaveTextContent(
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].emoji,
    );
  });

  it("renders nothing if qa status is not set", () => {
    render(
      <TestTable>
        <DirectoryColumnQA
          {...experiment}
          qaStatus={NimbusExperimentQAStatusEnum.NOT_SET}
        />
      </TestTable>,
    );
    expect(screen.queryByTestId("directory-table-cell-qa")).toHaveTextContent(
      "",
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
    ).toHaveTextContent(
      experiment
        .featureConfigs!.map((fc) => fc?.name)
        .sort()
        .join(", "),
    );
  });

  it("renders the None label if feature config is not present", () => {
    render(
      <TestTable>
        <DirectoryColumnFeature {...experiment} featureConfigs={[]} />
      </TestTable>,
    );
    expect(
      screen.getByTestId("directory-feature-config-none"),
    ).toBeInTheDocument();
  });
});

describe("DirectoryColumnApplication", () => {
  it("renders the application", () => {
    render(
      <TestTable>
        <DirectoryColumnApplication {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Desktop",
    );
  });
});

describe("DirectoryColumnChannel", () => {
  it("renders the channel", () => {
    render(
      <TestTable>
        <DirectoryColumnChannel {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Nightly",
    );
  });
});

describe("DirectoryColumnPopulationPercent", () => {
  it("renders the population percent", () => {
    render(
      <TestTable>
        <DirectoryColumnPopulationPercent {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "100%",
    );
  });
});

describe("DirectoryColumnFirefoxMinVersion", () => {
  it("renders the firefox min version", () => {
    render(
      <TestTable>
        <DirectoryColumnFirefoxMinVersion {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Firefox 80",
    );
  });
});

describe("DirectoryColumnFirefoxMaxVersion", () => {
  it("renders the firefox max version", () => {
    render(
      <TestTable>
        <DirectoryColumnFirefoxMaxVersion {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Firefox 64",
    );
  });
  it("renders no version if no max version is set", () => {
    render(
      <TestTable>
        <DirectoryColumnFirefoxMaxVersion
          {...experiment}
          firefoxMaxVersion={null}
        />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Not set",
    );
  });
});

describe("DirectoryColumneEnrollmentDate", () => {
  it("renders the enrollment date period", () => {
    render(
      <TestTable>
        <DirectoryColumnEnrollmentDate {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      getProposedEnrollmentRange(experiment),
    );
  });
  it("renders days if date is null for enrollment column", () => {
    render(
      <TestTable>
        <DirectoryColumnEnrollmentDate {...experiment} computedEndDate={null} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      getProposedEnrollmentRange(experiment),
    );
  });
});

describe("DirectoryColumnStartDate", () => {
  it("renders the start date", () => {
    render(
      <TestTable>
        <DirectoryColumnStartDate {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      humanDate(experiment.startDate!),
    );
  });
  it("renders not set start date", () => {
    render(
      <TestTable>
        <DirectoryColumnStartDate {...experiment} startDate={null} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Not set",
    );
  });
});

describe("DirectoryColumnEndDate", () => {
  it("renders the end date", () => {
    render(
      <TestTable>
        <DirectoryColumnEndDate {...experiment} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      humanDate(experiment.computedEndDate!),
    );
  });
  it("renders not set end date", () => {
    render(
      <TestTable>
        <DirectoryColumnEndDate {...experiment} computedEndDate={null} />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent(
      "Not set",
    );
  });
});

describe("DirectoryColumnUnpublishedUpdates", () => {
  it("renders unpublished updates badge when dirty", () => {
    render(
      <TestTable>
        <DirectoryColumnUnpublishedUpdates
          {...experiment}
          isRolloutDirty={true}
        />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent("YES");
  });

  it("renders blank unpublished updates when not dirty", () => {
    render(
      <TestTable>
        <DirectoryColumnUnpublishedUpdates
          {...experiment}
          isRolloutDirty={false}
        />
      </TestTable>,
    );
    expect(screen.getByTestId("directory-table-cell")).toHaveTextContent("");
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
  it("renders as expected without experiments", () => {
    render(
      <RouterSlugProvider>
        <DirectoryTable experiments={[]} />
      </RouterSlugProvider>,
    );
    expect(screen.getByTestId("no-experiments")).toBeInTheDocument();
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

describe("DirectoryTable", () => {
  it.each([
    ["looker link is present", experiment, "Looker"],
    [
      "rollouts link is present",
      {
        ...experiment,
        rolloutMonitoringDashboardUrl: "https",
      },
      "Rollout dashboard",
    ],
    [
      "results are ready",
      {
        ...experiment,
        showResultsUrl: true,
        monitoringDashboardUrl: null,
        rolloutMonitoringDashboardUrl: null,
      },
      "Results",
    ],
    [
      "neither is present",
      {
        ...experiment,
        monitoringDashboardUrl: null,
        rolloutMonitoringDashboardUrl: null,
      },
      "N/A",
    ],
    [
      "all are present",
      {
        ...experiment,
        showResultsUrl: true,
        resultsReady: true,
      },
      "LookerOpens in new windowRollout dashboardOpens in new windowResults",
    ],
  ])(
    "renders as expected with custom columns when %s",
    (_, experiment: getAllExperiments_experiments, expectedResult: string) => {
      render(
        <RouterSlugProvider>
          <DirectoryTable experiments={[experiment]} />
        </RouterSlugProvider>,
      );
      expectTableCells("directory-table-header", [
        "Name",
        "QA",
        "Owner",
        "Feature",
        "Application",
        "Channel",
        "Population %",
        "Min Version",
        "Max Version",
        "Start",
        "Enroll",
        "End",
        "Results",
        "Unpublished Updates",
      ]);
      expectTableCells("directory-table-cell", [
        experiment.name,
        experiment.owner!.username,
        experiment
          .featureConfigs!.map((fc) => fc?.name)
          .sort()
          .join(", "),
        "Desktop",
        "Desktop Nightly",
        experiment.populationPercent!.toString(),
        "Firefox 80",
        "Firefox 64",
        humanDate(experiment.startDate!),
        getProposedEnrollmentRange(experiment) as string,
        humanDate(experiment.computedEndDate!),
        expectedResult,
        "",
      ]);
    },
  );
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
