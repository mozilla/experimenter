/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import classNames from "classnames";
import React, { useCallback, useMemo } from "react";
import { Button } from "react-bootstrap";
import { UpdateSearchParams, useSearchParamsState } from "../../../hooks";
import { getProposedEnrollmentRange, humanDate } from "../../../lib/dateUtils";
import {
  enrollmentSortSelector,
  experimentSortComparator,
  ExperimentSortSelector,
  featureConfigNameSortSelector,
  ownerUsernameSortSelector,
  resultsReadySortSelector,
} from "../../../lib/experiment";
import { getAllExperiments_experiments } from "../../../types/getAllExperiments";
import LinkExternal from "../../LinkExternal";
import NotSet from "../../NotSet";

// These are all render functions for column types in the table.
export type ColumnComponent = React.FC<getAllExperiments_experiments>;

export const DirectoryColumnTitle: React.FC<getAllExperiments_experiments> = ({
  slug,
  name,
}) => {
  return (
    <td className="w-33" data-testid="directory-table-cell">
      <Link
        to={slug}
        data-sb-kind="pages/Summary"
        data-testid="directory-title-name"
      >
        {name}
      </Link>
      <br />
      <span
        className="text-monospace text-secondary small"
        data-testid="directory-title-slug"
      >
        {slug}
      </span>
    </td>
  );
};

export const DirectoryColumnOwner: ColumnComponent = (experiment) => (
  // #4380 made it so owner is never null, but we have experiments pre-this
  // that may be absent an owner, so keep this fallback in place.
  <td data-testid="directory-table-cell">
    {experiment.owner?.username || <NotSet />}
  </td>
);

export const DirectoryColumnFeature: ColumnComponent = ({ featureConfig }) => (
  <td data-testid="directory-table-cell">
    {featureConfig ? (
      <>
        <span data-testid="directory-feature-config-name">
          {featureConfig.name}
        </span>
        <br />
        <span
          className="text-monospace text-secondary small"
          data-testid="directory-feature-config-slug"
        >
          {featureConfig.slug}
        </span>
      </>
    ) : (
      <span data-testid="directory-feature-config-none">(None)</span>
    )}
  </td>
);

export const DirectoryColumnApplication: ColumnComponent = ({ featureConfig }) => (
  <td data-testid="directory-table-cell">
    {featureConfig ? (
      <>
        <span data-testid="directory-application-config-name">
          {featureConfig.name}
        </span>
      </>
    ) : (
      <span data-testid="directory-feature-config-none">(None)</span>
    )}
  </td>
);

export const DirectoryColumnChannel: ColumnComponent = ({ featureConfig }) => (
  <td data-testid="directory-table-cell">
    {featureConfig ? (
      <>
        <span data-testid="directory-channel-config-name">
          {featureConfig.name}
        </span>
      </>
    ) : (
      <span data-testid="directory-feature-config-none">(None)</span>
    )}
  </td>
);

export interface Column {
  /** The label of the column, which shows up in <th/> */
  label: string;
  /** Experiment property selector used for sorting the column */
  sortBy?: ExperimentSortSelector;
  /** A component that renders a <td/> given the experiment data */
  component: ColumnComponent;
}

export interface ColumnSortOrder {
  column: Column | undefined;
  descending: boolean;
}

interface ColumnTitleProps {
  column: Column;
}

export const ColumnTitle: React.FunctionComponent<ColumnTitleProps> = ({
  column: { label },
}) => (
  <th
    className="border-top-0 font-weight-normal"
    key={label}
    data-testid="directory-table-header"
  >
    {label}
  </th>
);

interface SortableColumnTitleProps {
  column: Column;
  columnSortOrder: ColumnSortOrder;
  updateSearchParams: UpdateSearchParams;
}

export const SortableColumnTitle: React.FunctionComponent<
  SortableColumnTitleProps
> = ({ column, columnSortOrder, updateSearchParams }) => {
  const { label } = column;
  const { descending } = columnSortOrder;
  const selected = columnSortOrder.column === column;

  const onClick = useCallback(() => {
    updateSearchParams((params) => {
      // tri-state sort: ascending -> descending -> reset
      if (!selected) {
        // 1) ascending
        params.set("sortByLabel", label);
        params.delete("descending");
      } else {
        if (!descending) {
          // 2) descending
          params.set("sortByLabel", label);
          params.set("descending", "1");
        } else {
          // 3) reset
          params.delete("sortByLabel");
          params.delete("descending");
        }
      }
    });
  }, [label, descending, selected, updateSearchParams]);

  return (
    <th
      className={classNames("border-top-0", {
        "sort-selected": selected,
        "sort-descending": selected && descending,
      })}
      key={label}
      data-testid="directory-table-header"
    >
      <Button
        variant="link"
        className="p-0 border-0"
        style={{ whiteSpace: "nowrap" }}
        onClick={onClick}
        title={label}
        data-testid="sort-select"
      >
        {label}
        <span style={{ display: "inline-block", width: "2em" }}>
          {selected ? (descending ? "▼" : "▲") : " "}
        </span>
      </Button>
    </th>
  );
};

interface DirectoryTableProps {
  experiments: getAllExperiments_experiments[];
  columns?: Column[];
}
// const { application, num_in_release, num_with_kpi_impact, cdou, other_business_goals } = sortByStatus(

const commonColumns: Column[] = [
  { 
    label: "Application", 
    component: DirectoryColumnApplication 
  },
  {
    label: "# in Release",
    component: DirectoryColumnOwner,
  },
  {
    label: "# with KPI impact",
    component: DirectoryColumnFeature,
  },
  {
    label: "CDoU",
    component: DirectoryColumnFeature,
  },
  {
    label: "Other business goals",
    component: DirectoryColumnFeature,
  },
];

const DirectoryTable: React.FunctionComponent<DirectoryTableProps> = ({
  experiments,
  columns = commonColumns,
}) => {
  const [searchParams, updateSearchParams] = useSearchParamsState();
  const columnSortOrder = useMemo(
    () => ({
      column: columns.find(
        (column) => column.label === searchParams.get("sortByLabel"),
      ),
      descending: searchParams.get("descending") === "1",
    }),
    [searchParams, columns],
  );

  const sortedExperiments = [...experiments];
  if (columnSortOrder.column && columnSortOrder.column.sortBy) {
    sortedExperiments.sort(
      experimentSortComparator(
        columnSortOrder.column.sortBy,
        columnSortOrder.descending,
      ),
    );
  }

  return (
    <div className="directory-table pb-2 mt-4">
      {experiments.length ? (
        <table className="table" data-testid="DirectoryTable">
          <thead>
            <tr>
              {columns.map((column, i) =>
                column.sortBy ? (
                  <SortableColumnTitle
                    key={column.label + i}
                    {...{ column, columnSortOrder, updateSearchParams }}
                  />
                ) : (
                  <ColumnTitle key={column.label + i} {...{ column }} />
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {sortedExperiments.map((experiment) => (
              <tr key={experiment.slug} data-testid="directory-table-row">
                {columns.map(({ label, component: ColumnComponent }, i) => {
                  return <ColumnComponent key={label + i} {...experiment} />;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p data-testid="no-experiments">No experiments found.</p>
      )}
    </div>
  );
};

export const DirectoryLiveTable: React.FC<DirectoryTableProps> = (props) => (
  <DirectoryTable
    {...props}
    columns={[
      ...commonColumns,
      {
        label: "Started",
        sortBy: "startDate",
        component: ({ startDate: d }) => (
          <td data-testid="directory-table-cell">{d && humanDate(d)}</td>
        ),
      },
      {
        label: "Enrolling",
        sortBy: enrollmentSortSelector,
        component: (experiment) => (
          <td data-testid="directory-table-cell">
            {getProposedEnrollmentRange(experiment)}
          </td>
        ),
      },
      {
        label: "Ending",
        sortBy: "computedEndDate",
        component: (experiment) => (
          <td data-testid="directory-table-cell">
            {humanDate(experiment.computedEndDate!)}
          </td>
        ),
      },
      {
        label: "Results",
        sortBy: resultsReadySortSelector,
        component: (experiment) => (
          <td data-testid="directory-table-cell">
            {experiment.monitoringDashboardUrl && (
              <LinkExternal
                href={experiment.monitoringDashboardUrl!}
                data-testid="link-monitoring-dashboard"
              >
                Looker
              </LinkExternal>
            )}
            {experiment.monitoringDashboardUrl && experiment.resultsReady && (
              <br />
            )}
            {experiment.resultsReady && (
              <Link
                to={`${experiment.slug}/results`}
                data-sb-kind="pages/Results"
              >
                Results
              </Link>
            )}
            {!experiment.monitoringDashboardUrl &&
              !experiment.resultsReady &&
              "N/A"}
          </td>
        ),
      },
    ]}
  />
);

export const DirectoryCompleteTable: React.FC<DirectoryTableProps> = (
  props,
) => (
  <DirectoryTable
    {...props}
    columns={[
      ...commonColumns,
      {
        label: "Started",
        sortBy: "startDate",
        component: ({ startDate: d }) => (
          <td data-testid="directory-table-cell">{d && humanDate(d)}</td>
        ),
      },
      {
        label: "Ended",
        sortBy: "computedEndDate",
        component: ({ computedEndDate: d }) => (
          <td data-testid="directory-table-cell">{d && humanDate(d)}</td>
        ),
      },
      {
        label: "Results",
        component: ({ slug }) => (
          <td data-testid="directory-table-cell">
            <Link to={`${slug}/results`} data-sb-kind="pages/Results">
              Results
            </Link>
          </td>
        ),
      },
    ]}
  />
);

export const DirectoryDraftsTable: React.FC<DirectoryTableProps> = (props) => (
  <DirectoryTable {...props} />
);

export default DirectoryTable;
