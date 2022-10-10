/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { Accordion, Button, Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { ReactComponent as CollapseMinus } from "../../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../../images/plus.svg";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { NimbusExperimentApplicationEnum } from "../../../types/globalTypes";
import { Code } from "../../Code";
import NotSet from "../../NotSet";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = ({ experiment }: TableAudienceProps) => {
  const { firefoxVersions, channels, targetingConfigs } = useConfig();
  const isDesktop =
    experiment.application === NimbusExperimentApplicationEnum.DESKTOP;

  const [expand, setExpand] = useState(false);

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
          <th>Maximum version</th>
          <td data-testid="experiment-ff-max">
            {displayConfigLabelOrNotSet(
              experiment.firefoxMaxVersion,
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
        {(isDesktop || experiment.locales.length > 0) && (
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
        )}
        {!isDesktop && (
          <tr>
            <th>Languages</th>
            <td data-testid="experiment-languages">
              {experiment.languages.length > 0 ? (
                <ul className="list-unstyled mb-0">
                  {experiment.languages.map((l) => (
                    <li key={l.id}>{l.name}</li>
                  ))}
                </ul>
              ) : (
                "All Languages"
              )}
            </td>
          </tr>
        )}
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
        <tr>
          <th>Sticky Enrollment</th>
          <td data-testid="experiment-is-sticky">
            {experiment.isSticky ? "True" : "False"}
          </td>
        </tr>
        <tr>
          <th>First Run Experiment</th>
          <td data-testid="experiment-is-first-run">
            {experiment.isFirstRun ? "True" : "False"}
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
        {experiment.recipeJson && (
          <tr id="recipe-json">
            <th>
              Recipe JSON <a href={`#recipe-json`}>#</a>
            </th>
            <td data-testid="experiment-recipe-json">
              <Accordion>
                <Accordion.Toggle
                  as={Accordion}
                  eventKey="0"
                  onClick={() => setExpand(!expand)}
                >
                  {expand ? (
                    <>
                      <div className="float-right">
                        <Button size="sm" variant="outline-primary">
                          <CollapseMinus />
                          Hide
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="float-right">
                        <Button size="sm" variant="outline-primary">
                          <ExpandPlus />
                          Show More
                        </Button>
                      </div>
                      <Code
                        codeString={
                          experiment.recipeJson.substring(0, 30) + "\n    ..."
                        }
                      />
                    </>
                  )}
                </Accordion.Toggle>

                <Accordion.Collapse eventKey="0">
                  <Code codeString={experiment.recipeJson} />
                </Accordion.Collapse>
              </Accordion>
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableAudience;
