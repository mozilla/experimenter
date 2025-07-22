/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import classNames from "classnames";
import React, { useCallback, useMemo } from "react";
import { Badge, Button, Table } from "react-bootstrap";
import LinkExternal from "src/components/LinkExternal";
import NotSet from "src/components/NotSet";
import { displayConfigLabelOrNotSet } from "src/components/Summary";
import { UpdateSearchParams, useConfig, useSearchParamsState } from "src/hooks";
import { QA_STATUS_PROPERTIES } from "src/lib/constants";
import { getProposedEnrollmentRange, humanDate } from "src/lib/dateUtils";
import {
  applicationSortSelector,
  channelSortSelector,
  computedEndDateSortSelector,
  enrollmentSortSelector,
  experimentSortComparator,
  ExperimentSortSelector,
  featureConfigNameSortSelector,
  firefoxMaxVersionSortSelector,
  firefoxMinVersionSortSelector,
  ownerUsernameSortSelector,
  populationPercentSortSelector,
  qaStatusSortSelector,
  resultsReadySortSelector,
  startDateSortSelector,
  unpublishedUpdatesSortSelector,
} from "src/lib/experiment";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";

// These are all render functions for column types in the table.
export type ColumnComponent = React.FC<getAllExperiments_experiments>;

export const DirectoryColumnTitle: React.FC<getAllExperiments_experiments> = ({
  slug,
  name,
}) => {
  return (
    <td data-testid="directory-table-cell">
      <Link
        to={slug}
        data-sb-kind="pages/Summary"
        data-testid="directory-title-name"
      >
        {name}
      </Link>
    </td>
  );
};

export const DirectoryColumnQA: ColumnComponent = ({ qaStatus }) => (
  <td
    title={qaStatus ? QA_STATUS_PROPERTIES[qaStatus].description : ""}
    data-testid="directory-table-cell-qa"
  >
    {qaStatus && QA_STATUS_PROPERTIES[qaStatus].emoji}
  </td>
);

export const DirectoryColumnOwner: ColumnComponent = (experiment) => (
  // #4380 made it so owner is never null, but we have experiments pre-this
  // that may be absent an owner, so keep this fallback in place.
  <td data-testid="directory-table-cell">
    {experiment.owner?.username || <NotSet />}
  </td>
);

export const DirectoryColumnApplication: ColumnComponent = (experiment) => {
  const { applications } = useConfig();
  return (
    <td data-testid="directory-table-cell" className="text-capitalize">
      {displayConfigLabelOrNotSet(experiment.application, applications)}
    </td>
  );
};
export const DirectoryColumnChannel: ColumnComponent = (experiment) => {
  const { channels } = useConfig();
  return (
    <td data-testid="directory-table-cell" className="text-capitalize">
      {displayConfigLabelOrNotSet(experiment.channel, channels)}
    </td>
  );
};

export const DirectoryColumnPopulationPercent: ColumnComponent = (
  experiment,
) => (
  <td data-testid="directory-table-cell">
    {`${Math.round(Number(experiment.populationPercent!))}%`}
  </td>
);

export const DirectoryColumnFirefoxMinVersion: ColumnComponent = (
  experiment,
) => {
  const { firefoxVersions } = useConfig();
  return (
    <td data-testid="directory-table-cell" className="text-capitalize">
      {displayConfigLabelOrNotSet(
        experiment.firefoxMinVersion,
        firefoxVersions,
      )}
    </td>
  );
};
export const DirectoryColumnFirefoxMaxVersion: ColumnComponent = (
  experiment,
) => {
  const { firefoxVersions } = useConfig();
  return (
    <td data-testid="directory-table-cell" className="text-capitalize">
      {displayConfigLabelOrNotSet(
        experiment.firefoxMaxVersion,
        firefoxVersions,
      )}
    </td>
  );
};

export const DirectoryColumnFeature: ColumnComponent = ({ featureConfigs }) => (
  <td data-testid="directory-table-cell">
    {featureConfigs?.length ? (
      <>
        <span data-testid="directory-feature-config-name">
          {featureConfigs
            .map((fc) => fc?.name)
            .sort()
            .join(", ")}
        </span>
      </>
    ) : (
      <span data-testid="directory-feature-config-none">(None)</span>
    )}
  </td>
);

export const DirectoryColumnStartDate: ColumnComponent = ({ startDate: d }) => (
  <td data-testid="directory-table-cell">
    {(d && humanDate(d)) || <NotSet />}
  </td>
);

export const DirectoryColumnEnrollmentDate: ColumnComponent = (experiment) => (
  <td data-testid="directory-table-cell">
    {getProposedEnrollmentRange(experiment) || <NotSet />}
  </td>
);

export const DirectoryColumnEndDate: ColumnComponent = ({
  computedEndDate: d,
}) => (
  <td data-testid="directory-table-cell">
    {(d && humanDate(d)) || <NotSet />}
  </td>
);

export const DirectoryColumnUnpublishedUpdates: ColumnComponent = ({
  isRolloutDirty: d,
}) => (
  <td data-testid="directory-table-cell">
    {d ? (
      <>
        <Badge
          className={
            "ml-2 border rounded-pill px-2 bg-white font-weight-normal border-danger text-danger"
          }
          data-testid="directory-unpublished-updates"
        >
          {d ? "YES" : ""}
        </Badge>
      </>
    ) : (
      ""
    )}
  </td>
);

export const DirectoryColumnResults: ColumnComponent = (experiment) => (
  <td data-testid="directory-table-cell">
    {experiment.monitoringDashboardUrl && (
      <LinkExternal
        href={experiment.monitoringDashboardUrl!}
        data-testid="link-monitoring-dashboard"
      >
        Looker
      </LinkExternal>
    )}
    {experiment.monitoringDashboardUrl &&
      experiment.rolloutMonitoringDashboardUrl && <br />}
    {experiment.rolloutMonitoringDashboardUrl && (
      <LinkExternal
        href={experiment.rolloutMonitoringDashboardUrl!}
        data-testid="link-rollout-monitoring-dashboard"
      >
        Rollout dashboard
      </LinkExternal>
    )}
    {experiment.monitoringDashboardUrl && experiment.showResultsUrl && <br />}
    {experiment.showResultsUrl && (
      <Link to={`${experiment.slug}/results`} data-sb-kind="pages/Results">
        Results
      </Link>
    )}
    {!experiment.monitoringDashboardUrl &&
      !experiment.rolloutMonitoringDashboardUrl &&
      !experiment.showResultsUrl &&
      "N/A"}
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

const commonColumns: Column[] = [
  { label: "Name", sortBy: "name", component: DirectoryColumnTitle },
  {
    label: "QA",
    sortBy: qaStatusSortSelector,
    component: DirectoryColumnQA,
  },
  {
    label: "Owner",
    sortBy: ownerUsernameSortSelector,
    component: DirectoryColumnOwner,
  },
  {
    label: "Feature",
    sortBy: featureConfigNameSortSelector,
    component: DirectoryColumnFeature,
  },
  {
    label: "Application",
    sortBy: applicationSortSelector,
    component: DirectoryColumnApplication,
  },
  {
    label: "Channel",
    sortBy: channelSortSelector,
    component: DirectoryColumnChannel,
  },
  {
    label: "Population %",
    sortBy: populationPercentSortSelector,
    component: DirectoryColumnPopulationPercent,
  },
  {
    label: "Min Version",
    sortBy: firefoxMinVersionSortSelector,
    component: DirectoryColumnFirefoxMinVersion,
  },
  {
    label: "Max Version",
    sortBy: firefoxMaxVersionSortSelector,
    component: DirectoryColumnFirefoxMaxVersion,
  },
  {
    label: "Start",
    sortBy: startDateSortSelector,
    component: DirectoryColumnStartDate,
  },
  {
    label: "Enroll",
    sortBy: enrollmentSortSelector,
    component: DirectoryColumnEnrollmentDate,
  },
  {
    label: "End",
    sortBy: computedEndDateSortSelector,
    component: DirectoryColumnEndDate,
  },
  {
    label: "Results",
    sortBy: resultsReadySortSelector,
    component: DirectoryColumnResults,
  },
  {
    label: "Unpublished Updates",
    sortBy: unpublishedUpdatesSortSelector,
    component: DirectoryColumnUnpublishedUpdates,
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
    <>
      {experiments.length ? (
        <Table
          data-testid="DirectoryTable"
          className="directory-table"
          size="sm"
          responsive
          hover
          style={{ width: "100%" }}
        >
          <thead>
            <tr>
              {columns.map((column, i) => (
                <SortableColumnTitle
                  key={column.label + i}
                  {...{ column, columnSortOrder, updateSearchParams }}
                />
              ))}
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
        </Table>
      ) : (
        <p data-testid="no-experiments">No experiments found.</p>
      )}
    </>
  );
};

export default DirectoryTable;
