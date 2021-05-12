/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig, useOutcomes } from "../../../hooks";
import { ReactComponent as ExternalIcon } from "../../../images/external.svg";
import { RISK_QUESTIONS } from "../../../lib/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import LinkExternal from "../../LinkExternal";
import NotSet from "../../NotSet";
import RichText from "../../RichText";

type TableSummaryProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const getRiskLabel = (answer: boolean) => (answer ? "Yes" : "No");

const TableSummary = ({ experiment }: TableSummaryProps) => {
  const {
    application,
    documentationLink: configDocumentationLinks,
  } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  return (
    <Table bordered data-testid="table-summary" className="mb-4">
      <tbody>
        <tr>
          <th className="w-33">Slug</th>
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
            {displayConfigLabelOrNotSet(experiment.application, application)}
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
        {experiment.riskMitigationLink && (
          <tr>
            <th>Risk mitigation checklist</th>
            <td data-testid="experiment-risk-mitigation-link">
              <LinkExternal href={experiment.riskMitigationLink}>
                <span className="mr-1 align-middle">
                  {experiment.riskMitigationLink}
                </span>
                <ExternalIcon />
              </LinkExternal>
            </td>
          </tr>
        )}
        <tr>
          <th>Risk mitigation question (1):</th>
          <td>
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
          <td>
            {RISK_QUESTIONS.PARTNER} —{" "}
            {experiment.riskPartnerRelated !== null ? (
              getRiskLabel(experiment.riskPartnerRelated)
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        <tr>
          <th>Risk mitigation question (3):</th>
          <td>
            {RISK_QUESTIONS.REVENUE} —{" "}
            {experiment.riskRevenue !== null ? (
              getRiskLabel(experiment.riskRevenue)
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        {experiment.documentationLinks &&
          experiment.documentationLinks?.length > 0 && (
            <tr>
              <th>Additional links</th>
              <td data-testid="experiment-additional-links">
                {experiment.documentationLinks.map((documentationLink, idx) => (
                  <LinkExternal
                    href={documentationLink.link}
                    data-testid="experiment-additional-link"
                    key={`doc-link-${idx}`}
                    className="d-block"
                  >
                    <span className="mr-1 align-middle">
                      {
                        configDocumentationLinks!.find(
                          (d) => d?.value === documentationLink.title,
                        )?.label
                      }
                    </span>
                    <ExternalIcon />
                  </LinkExternal>
                ))}
              </td>
            </tr>
          )}
        <tr>
          <th>Feature config</th>
          <td data-testid="experiment-feature-config">
            {experiment.featureConfig?.name ? (
              experiment.featureConfig.name
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
      </tbody>
    </Table>
  );
};

export default TableSummary;
