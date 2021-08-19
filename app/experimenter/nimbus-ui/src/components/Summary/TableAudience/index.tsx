/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useMemo } from "react";
import { Table } from "react-bootstrap";
import ReactJson from "react-json-view";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { Code } from "../../Code";
import NotSet from "../../NotSet";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = ({ experiment }: TableAudienceProps) => {
  const { firefoxMinVersion, channel, targetingConfigSlug } = useConfig();

  const recipeJsonParsed = useMemo(() => {
    if (experiment.recipeJson) {
      return JSON.parse(experiment.recipeJson);
    }
  }, [experiment.recipeJson]);

  return (
    <Table bordered data-testid="table-audience" className="mb-4 table-fixed">
      <tbody>
        <tr>
          <th className="w-33">Channel</th>
          <td data-testid="experiment-channel">
            {displayConfigLabelOrNotSet(experiment.channel, channel)}
          </td>
        </tr>
        <tr>
          <th>Minimum version</th>
          <td data-testid="experiment-ff-min">
            {displayConfigLabelOrNotSet(
              experiment.firefoxMinVersion,
              firefoxMinVersion,
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
                targetingConfigSlug,
              )}
            </td>
          </tr>
        )}
        <tr>
          <th>Locales</th>
          <td data-testid="experiment-locales">
            {experiment.locales.length > 0
              ? experiment.locales.map((l) => l.name).join(", ")
              : "All locales"}
          </td>
        </tr>
        <tr>
          <th>Countries</th>
          <td data-testid="experiment-countries">
            {experiment.countries.length > 0
              ? experiment.countries.map((c) => c.name).join(", ")
              : "All countries"}
          </td>
        </tr>
        {experiment.jexlTargetingExpression &&
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
        {recipeJsonParsed && (
          <tr>
            <th>Recipe JSON</th>
            <td data-testid="experiment-recipe-json">
              <ReactJson
                src={recipeJsonParsed}
                collapsed={1}
                displayDataTypes={false}
                displayObjectSize={false}
              />
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableAudience;
