/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Card, Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig, useOutcomes } from "../../../hooks";
import { RISK_QUESTIONS } from "../../../lib/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import NotSet from "../../NotSet";
import RichText from "../../RichText";

type TableOverviewProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const getRiskLabel = (answer: boolean) => (answer ? "Yes" : "No");

const TableOverview = ({ experiment }: TableOverviewProps) => {
  const { applications } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  return (
    <Card border="light" className="mb-4" bg="light">
      <Card.Header as="h5">Overview</Card.Header>
      <Card.Body>
        <Table data-testid="table-overview">
          <tbody>
            <tr>
              <th>Slug</th>
              <td data-testid="experiment-slug" className="text-monospace">
                {experiment.slug}
              </td>

              <th>Experiment owner</th>
              <td data-testid="experiment-owner">
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
            <tr></tr>

            <tr>
              <th>Risk mitigation question (1):</th>
              <td
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-1"
              >
                {RISK_QUESTIONS.BRAND} —{" "}
                {experiment.riskBrand !== null ? (
                  getRiskLabel(experiment.riskBrand)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Risk mitigation question (2):</th>
              <td
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-2"
              >
                {RISK_QUESTIONS.REVENUE} —{" "}
                {experiment.riskRevenue !== null ? (
                  getRiskLabel(experiment.riskRevenue)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Risk mitigation question (3):</th>
              <td
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-3"
              >
                {RISK_QUESTIONS.PARTNER} —{" "}
                {experiment.riskPartnerRelated !== null ? (
                  getRiskLabel(experiment.riskPartnerRelated)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>

            {primaryOutcomes.length > 0 && (
              <tr>
                <th>Primary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-primary">
                  {primaryOutcomes
                    .map((outcome) => outcome?.friendlyName)
                    .join(", ")}
                </td>
              </tr>
            )}
            {secondaryOutcomes.length > 0 && (
              <tr>
                <th>Secondary outcomes</th>
                <td colSpan={3} data-testid="experiment-outcome-secondary">
                  {secondaryOutcomes
                    .map((outcome) => outcome?.friendlyName)
                    .join(", ")}
                </td>
              </tr>
            )}
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableOverview;
