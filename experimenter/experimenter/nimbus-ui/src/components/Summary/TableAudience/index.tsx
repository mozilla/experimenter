/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { Accordion, Button, Card, Table } from "react-bootstrap";
import { Code } from "src/components/Code";
import NotSet from "src/components/NotSet";
import { MOBILE_APPLICATIONS } from "src/components/PageEditAudience/FormAudience";
import { displayConfigLabelOrNotSet } from "src/components/Summary";
import { useConfig } from "src/hooks";
import { ReactComponent as CollapseMinus } from "src/images/minus.svg";
import { ReactComponent as ExpandPlus } from "src/images/plus.svg";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment,
  getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment,
} from "src/types/getExperiment";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

type TableAudienceProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableAudience = ({ experiment }: TableAudienceProps) => {
  const { firefoxVersions, channels, targetingConfigs } = useConfig();
  const isDesktop =
    experiment.application === NimbusExperimentApplicationEnum.DESKTOP;
  const isMobile =
    experiment.application != null &&
    MOBILE_APPLICATIONS.includes(experiment.application);

  const [expand, setExpand] = useState(false);

  return (
    <Card className="border-left-0 border-right-0 border-bottom-0">
      <Card.Header as="h5">Audience</Card.Header>
      <Card.Body>
        <Table data-testid="table-audience" className="table-fixed">
          <tbody>
            <tr>
              <th className="border-top-0">Channel</th>
              <td data-testid="experiment-channel" className="border-top-0">
                {displayConfigLabelOrNotSet(experiment.channel, channels)}
              </td>

              {experiment.targetingConfigSlug && (
                <>
                  <th className="border-top-0">Advanced Targeting</th>
                  <td data-testid="experiment-target" className="border-top-0">
                    {displayConfigLabelOrNotSet(
                      experiment.targetingConfigSlug,
                      targetingConfigs,
                    )}
                  </td>
                </>
              )}
            </tr>
            <tr>
              <th>Minimum version</th>
              <td data-testid="experiment-ff-min">
                {displayConfigLabelOrNotSet(
                  experiment.firefoxMinVersion,
                  firefoxVersions,
                )}
              </td>
              <th>Maximum version</th>
              <td data-testid="experiment-ff-max">
                {displayConfigLabelOrNotSet(
                  experiment.firefoxMaxVersion,
                  firefoxVersions,
                )}
              </td>
            </tr>
            <tr>
              {(isDesktop || experiment.locales.length > 0) && (
                <>
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
                </>
              )}
              {!isDesktop && (
                <>
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
                </>
              )}

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
              <th>Expected enrolled clients</th>
              <td data-testid="experiment-total-enrolled">
                {experiment.totalEnrolledClients
                  ? experiment.totalEnrolledClients.toLocaleString()
                  : "0"}
              </td>

              <th>Population %</th>
              <td data-testid="experiment-population">
                {experiment.populationPercent ? (
                  `${Number(experiment.populationPercent).toFixed(1)}%`
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>

            <tr>
              <th>Sticky Enrollment</th>
              <td data-testid="experiment-is-sticky">
                {experiment.isSticky ? "True" : "False"}
              </td>

              {isMobile ? (
                <>
                  <th>First Run Experiment</th>
                  <td data-testid="experiment-is-first-run">
                    {experiment.isFirstRun ? "True" : "False"}
                  </td>
                </>
              ) : (
                <td colSpan={2}></td>
              )}
            </tr>
            {isMobile && (
              <tr>
                <th>First Run Release Date</th>
                <td colSpan={3} data-testid="experiment-release-date">
                  {experiment.proposedReleaseDate ? (
                    experiment.proposedReleaseDate
                  ) : (
                    <NotSet color="primary" />
                  )}
                </td>
              </tr>
            )}
            <tr>
              <th>Required Experiments</th>
              <td>
                <ExperimentList
                  experimentsBranches={experiment.requiredExperimentsBranches.map(
                    (eb) => ({
                      experiment: eb.requiredExperiment,
                      branchSlug: eb.branchSlug,
                    }),
                  )}
                />
              </td>
              <th>Excluded Experiments</th>
              <td>
                <ExperimentList
                  experimentsBranches={experiment.excludedExperimentsBranches.map(
                    (eb) => ({
                      experiment: eb.excludedExperiment,
                      branchSlug: eb.branchSlug,
                    }),
                  )}
                />
              </td>
            </tr>

            {experiment.jexlTargetingExpression &&
            experiment.jexlTargetingExpression !== "" ? (
              <tr>
                <th>Full targeting expression</th>
                <td
                  colSpan={3}
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
                <td colSpan={3} data-testid="experiment-recipe-json">
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
                              experiment.recipeJson.substring(0, 30) +
                              "\n    ..."
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
      </Card.Body>
    </Card>
  );
};

interface ExperimentListProps {
  experimentsBranches: {
    experiment:
      | getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment
      | getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment;
    branchSlug: string | null;
  }[];
}
function ExperimentList({ experimentsBranches }: ExperimentListProps) {
  if (experimentsBranches.length === 0) {
    return <span>None</span>;
  }

  return (
    <>
      {experimentsBranches.map((experimentBranch) => {
        const branchLabel = experimentBranch.branchSlug
          ? `${experimentBranch.branchSlug} branch`
          : "All branches";
        return (
          <p key={experimentBranch.experiment.slug}>
            <a href={`/nimbus/${experimentBranch.experiment.slug}/summary`}>
              {experimentBranch.experiment.name} ({branchLabel})
            </a>
          </p>
        );
      })}
    </>
  );
}

export default TableAudience;
