/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig, useOutcomes } from "../../../hooks";
import { RISK_QUESTIONS } from "../../../lib/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import NotSet from "../../NotSet";
import RichText from "../../RichText";

type TableOverviewProps = {
  experiment: getExperiment_experimentBySlug;
  withFullDetails?: boolean;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const getRiskLabel = (answer: boolean) => (answer ? "Yes" : "No");

const TableOverview = ({
  experiment,
  withFullDetails = true,
}: TableOverviewProps) => {
  const { applications } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  return (
    <Table data-testid="table-overview" className="mb-4 border rounded">
      <tbody>
        <tr>
          <th className="w-25">Slug</th>
          <td data-testid="experiment-slug" className="text-monospace">
            {experiment.slug}
          </td>
        </tr>
        <tr>
          <th>Experiment owner</th>
          <td data-testid="experiment-owner">
            {experiment.owner ? experiment.owner.email : <NotSet />}
          </td>
        </tr>
        <tr>
          <th>Application</th>
          <td data-testid="experiment-application">
            {displayConfigLabelOrNotSet(experiment.application, applications)}
          </td>
        </tr>
        <tr>
          <th>Hypothesis</th>
          <td data-testid="experiment-hypothesis">
            <RichText text={experiment.hypothesis || ""} />
          </td>
        </tr>
        <tr>
          <th>Public description</th>
          <td data-testid="experiment-description">
            {experiment.publicDescription ? (
              experiment.publicDescription
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        {withFullDetails && (
          <>
            <tr>
              <th>Risk mitigation question (1):</th>
              <td data-testid="experiment-risk-mitigation-question-1">
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
              <td data-testid="experiment-risk-mitigation-question-2">
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
              <td data-testid="experiment-risk-mitigation-question-3">
                {RISK_QUESTIONS.PARTNER} —{" "}
                {experiment.riskPartnerRelated !== null ? (
                  getRiskLabel(experiment.riskPartnerRelated)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>Feature config</th>
              <td data-testid="experiment-feature-config">
                {experiment.featureConfigs?.length ? (
                  experiment.featureConfigs.map((f) => f.name).join(", ")
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            {primaryOutcomes.length > 0 && (
              <tr>
                <th>Primary outcomes</th>
                <td data-testid="experiment-outcome-primary">
                  {primaryOutcomes
                    .map((outcome) => outcome?.friendlyName)
                    .join(", ")}
                </td>
              </tr>
            )}
            {secondaryOutcomes.length > 0 && (
              <tr>
                <th>Secondary outcomes</th>
                <td data-testid="experiment-outcome-secondary">
                  {secondaryOutcomes
                    .map((outcome) => outcome?.friendlyName)
                    .join(", ")}
                </td>
              </tr>
            )}
          </>
        )}
      </tbody>
    </Table>
  );
};

export default TableOverview;
