/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { Code } from "../../Code";
import NotSet from "../../NotSet";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
  withFullDetails?: boolean;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = ({
  experiment,
  withFullDetails = true,
}: TableAudienceProps) => {
  const { firefoxVersions, channels, targetingConfigs } = useConfig();

  return (
    <Table
      data-testid="table-audience"
      className="mb-4 table-fixed border rounded"
    >
      <tbody>
        <tr>
          <th className="w-25">Channel</th>
          <td data-testid="experiment-channel">
            {displayConfigLabelOrNotSet(experiment.channel, channels)}
          </td>
        </tr>
        <tr>
          <th>Minimum version</th>
          <td data-testid="experiment-ff-min">
            {displayConfigLabelOrNotSet(
              experiment.firefoxMinVersion,
              firefoxVersions,
            )}
          </td>
        </tr>
        <tr>
          <th>Population %</th>
          <td data-testid="experiment-population">
            {experiment.populationPercent ? (
              `${experiment.populationPercent}%`
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        {experiment.totalEnrolledClients > 0 && (
          <tr>
            <th>Expected enrolled clients</th>
            <td data-testid="experiment-total-enrolled">
              {experiment.totalEnrolledClients.toLocaleString()}
            </td>
          </tr>
        )}
        {experiment.targetingConfigSlug && (
          <tr>
            <th>Advanced Targeting</th>
            <td data-testid="experiment-target">
              {displayConfigLabelOrNotSet(
                experiment.targetingConfigSlug,
                targetingConfigs,
              )}
            </td>
          </tr>
        )}
        <tr>
          <th>Locales</th>
          <td data-testid="experiment-locales">
            {experiment.locales.length > 0 ? (
              <ul className="list-unstyled mb-0">
                {experiment.locales.map((l) => (
                  <li key={l.id}>{l.name}</li>
                ))}
              </ul>
            ) : (
              "All locales"
            )}
          </td>
        </tr>
        <tr>
          <th>Countries</th>
          <td data-testid="experiment-countries">
            {experiment.countries.length > 0 ? (
              <ul className="list-unstyled mb-0">
                {experiment.countries.map((c) => (
                  <li key={c.id}>{c.name}</li>
                ))}
              </ul>
            ) : (
              "All countries"
            )}
          </td>
        </tr>
        {withFullDetails &&
        experiment.jexlTargetingExpression &&
        experiment.jexlTargetingExpression !== "" ? (
          <tr>
            <th>Full targeting expression</th>
            <td
              data-testid="experiment-target-expression"
              className="text-monospace"
            >
              <Code
                className="text-wrap"
                codeString={experiment.jexlTargetingExpression}
              />
            </td>
          </tr>
        ) : null}
        {withFullDetails && experiment.recipeJson && (
          <tr id="recipe-json">
            <th>
              Recipe JSON <a href={`#recipe-json`}>#</a>
            </th>
            <td data-testid="experiment-recipe-json">
              <Code codeString={experiment.recipeJson} />
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableAudience;
