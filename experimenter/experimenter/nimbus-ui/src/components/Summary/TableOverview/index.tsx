/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Card, Table } from "react-bootstrap";
import NotSet from "src/components/NotSet";
import RichText from "src/components/RichText";
import { displayConfigLabelOrNotSet } from "src/components/Summary";
import { useConfig, useOutcomes } from "src/hooks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type TableOverviewProps = {
  experiment: getExperiment_experimentBySlug;
};

interface DocSlugs {
  [key: string]: string;
}

// `<tr>`s showing optional fields that are not set are not displayed.

const TableOverview = ({ experiment }: TableOverviewProps) => {
  const { applications } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  const docSlugs: DocSlugs = {
    DESKTOP: "firefox_desktop",
    FENIX: "fenix",
    IOS: "firefox_ios",
  };

  const primaryOutcomeWithLinks =
    primaryOutcomes.length > 0 &&
    primaryOutcomes
      .map((outcome, index) => (
        <a
          key={index}
          target="_blank"
          data-testid={`primary-outcome-${outcome?.slug}`}
          href={`https://mozilla.github.io/metric-hub/outcomes/${
            docSlugs[outcome?.application ?? ""]
          }/${outcome?.slug}`}
          rel="noreferrer"
        >
          {outcome?.friendlyName}
        </a>
      ))
      .reduce((acc, curr) => (
        <>
          {acc}, {curr}
        </>
      ));

  const secondaryOutcomeWithLinks =
    secondaryOutcomes.length > 0 &&
    secondaryOutcomes
      .map((outcome, index) => (
        <a
          key={index}
          target="_blank"
          data-testid={`secondary-outcome-${outcome?.slug}`}
          href={`https://mozilla.github.io/metric-hub/outcomes/${
            docSlugs[outcome?.application ?? ""]
          }/${outcome?.slug}`}
          rel="noreferrer"
        >
          {outcome?.friendlyName}
        </a>
      ))
      .reduce((acc, curr) => (
        <>
          {acc}, {curr}
        </>
      ));

  return (
    <Card className="my-4 border-left-0 border-right-0 border-bottom-0">
      <Card.Header as="h5">Overview</Card.Header>
      <Card.Body>
        <Table data-testid="table-overview">
          <tbody>
            <tr>
              <th className="border-top-0">Slug</th>
              <td
                data-testid="experiment-slug"
                className="text-monospace border-top-0"
              >
                {experiment.slug}
              </td>

              <th className="border-top-0">Experiment owner</th>
              <td data-testid="experiment-owner" className="border-top-0">
                {experiment.owner ? experiment.owner.email : <NotSet />}
              </td>
            </tr>
            <tr>
              <th>Application</th>
              <td data-testid="experiment-application">
                {displayConfigLabelOrNotSet(
                  experiment.application,
                  applications,
                )}
              </td>
              <th>Public description</th>
              <td data-testid="experiment-description">
                {experiment.publicDescription ? (
                  experiment.publicDescription
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Feature config</th>
              <td data-testid="experiment-feature-config">
                {experiment.featureConfigs?.length ? (
                  experiment.featureConfigs.map((f, idx) => (
                    <React.Fragment key={f?.id || idx}>
                      <p>
                        {f?.name}
                        {f?.description?.length ? `- ${f.description}` : ""}
                      </p>
                    </React.Fragment>
                  ))
                ) : (
                  <NotSet />
                )}
              </td>

              <th>Advanced Targeting</th>
              <td data-testid="experiment-targeting-config">
                {experiment.targetingConfig?.length ? (
                  experiment.targetingConfig.map((t) => (
                    <p key={t?.label}>{`${t?.label} - ${t?.description}`}</p>
                  ))
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Hypothesis</th>
              <td colSpan={3} data-testid="experiment-hypothesis">
                <RichText text={experiment.hypothesis || ""} />
              </td>
            </tr>

            {primaryOutcomes.length > 0 && (
              <tr>
                <th>Primary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-primary">
                  {primaryOutcomeWithLinks}
                </td>
              </tr>
            )}
            {secondaryOutcomes.length > 0 && (
              <tr>
                <th>Secondary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-secondary">
                  {secondaryOutcomeWithLinks}
                </td>
              </tr>
            )}

            <tr>
              <th>Team Projects</th>
              <td colSpan={3} data-testid="experiment-team-projects">
                {experiment.projects!.length > 0 ? (
                  <ul className="list-unstyled mb-0">
                    {experiment.projects!.map((l) => (
                      <li key={l!.id}>{l!.name}</li>
                    ))}
                  </ul>
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableOverview;
