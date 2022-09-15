/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import classNames from "classnames";
import React, { useCallback, useMemo } from "react";
import { Button } from "react-bootstrap";
import {
  UpdateSearchParams,
  useConfig,
  useSearchParamsState,
} from "../../../hooks";
import { getProposedEnrollmentRange, humanDate } from "../../../lib/dateUtils";
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
  resultsReadySortSelector,
  startDateSortSelector,
} from "../../../lib/experiment";
import { getAllExperiments_experiments } from "../../../types/getAllExperiments";
import LinkExternal from "../../LinkExternal";
import NotSet from "../../NotSet";
import { displayConfigLabelOrNotSet } from "../../Summary";

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
    {experiment.populationPercent! || <NotSet />}
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

export const DirectoryColumnFeature: ColumnComponent = ({ featureConfig }) => (
  <td data-testid="directory-table-cell">
    {featureConfig ? (
      <>
        <span data-testid="directory-feature-config-name">
          {featureConfig.name}
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
    {experiment.monitoringDashboardUrl && experiment.resultsReady && <br />}
    {!experiment.isRollout && experiment.resultsReady && (
      <Link to={`${experiment.slug}/results`} data-sb-kind="pages/Results">
        Results
      </Link>
    )}
    {!experiment.monitoringDashboardUrl &&
      !experiment.rolloutMonitoringDashboardUrl &&
      !experiment.resultsReady &&
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
    <div
      className="directory-table pb-2 mt-4"
      style={{ width: "auto", maxWidth: "100%" }}
    >
      {experiments.length ? (
        <table className="table" data-testid="DirectoryTable">
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
        </table>
      ) : (
        <p data-testid="no-experiments">No experiments found.</p>
      )}
    </div>
  );
};

export default DirectoryTable;
