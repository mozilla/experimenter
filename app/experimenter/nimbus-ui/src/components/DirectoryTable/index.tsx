/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import "./index.scss";
import { Link } from "@reach/router";
import LinkExternal from "../LinkExternal";
import {
  getProposedEndDate,
  getProposedEnrollmentRange,
  humanDate,
} from "../../lib/dateUtils";

// These are all render functions for column type sin the table.
export type ColumnComponent = React.FC<getAllExperiments_experiments>;

export const DirectoryColumnTitle: ColumnComponent = ({ slug, name }) => {
  return (
    <td className="w-33">
      <Link to={slug} data-sb-kind="pages/Summary">
        {name}
      </Link>
      <br />
      <span className="text-monospace text-secondary small">{slug}</span>
    </td>
  );
};

export const DirectoryColumnOwner: ColumnComponent = ({ owner }) => (
  <td>{owner && owner.username}</td>
);

export const DirectoryColumnFeature: ColumnComponent = ({ featureConfig }) => (
  <td>
    {featureConfig ? (
      <>
        {featureConfig.name}
        <br />
        <span className="text-monospace text-secondary small">
          {featureConfig.slug}
        </span>
      </>
    ) : (
      "Simple"
    )}
  </td>
);

interface Column {
  /** The label of the column, which shows up in <th/> */
  label: string;
  /** A component that renders a <td/> given the experiment data */
  component: ColumnComponent;
}

interface DirectoryTableProps {
  title: string;
  experiments: getAllExperiments_experiments[];
  columns?: Column[];
}

const DirectoryTable: React.FunctionComponent<DirectoryTableProps> = ({
  title,
  experiments,
  columns: customColumns = [],
}) => {
  const columns = [
    // All directory views start with these three columns...
    { label: title, component: DirectoryColumnTitle },
    { label: "Owner", component: DirectoryColumnOwner },
    { label: "Feature", component: DirectoryColumnFeature },

    // And add any additional ones.
    ...customColumns,
  ];
  return (
    <div className="directory-table pb-4" data-testid="DirectoryTable">
      <table className="table">
        <thead>
          <tr>
            {columns.map(({ label }) => (
              <th key={label}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {experiments.length ? (
            experiments.map((experiment) => (
              <tr key={experiment.slug}>
                {columns.map(({ label, component: ColumnComponent }, i) => {
                  return <ColumnComponent key={label + i} {...experiment} />;
                })}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>No experiments found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export const DirectoryLiveTable: React.FC<DirectoryTableProps> = (props) => (
  <DirectoryTable
    {...props}
    columns={[
      {
        label: "Enrolling",
        component: (experiment) => (
          <td>{getProposedEnrollmentRange(experiment)}</td>
        ),
      },
      {
        label: "Ending",
        component: (experiment) => <td>{getProposedEndDate(experiment)}</td>,
      },
      {
        label: "Monitoring",
        component: ({ monitoringDashboardUrl }) => (
          <td>
            {monitoringDashboardUrl && (
              <LinkExternal
                href={monitoringDashboardUrl!}
                data-testid="link-monitoring-dashboard"
              >
                Grafana
              </LinkExternal>
            )}
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
      {
        label: "Started",
        component: ({ startDate: d }) => <td>{d && humanDate(d)}</td>,
      },
      {
        label: "Ended",
        component: ({ endDate: d }) => <td>{d && humanDate(d)}</td>,
      },
      {
        label: "Results",
        component: ({ slug }) => (
          <td>
            <Link to={`${slug}/results`} data-sb-kind="pages/Results">
              results
            </Link>
          </td>
        ),
      },
    ]}
  />
);

export default DirectoryTable;
