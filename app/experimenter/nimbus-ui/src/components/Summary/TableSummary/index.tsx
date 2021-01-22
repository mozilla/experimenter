/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { ReactComponent as ExternalIcon } from "../../../images/external.svg";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import LinkExternal from "../../LinkExternal";
import NotSet from "../../NotSet";
import RichText from "../../RichText";

type TableSummaryProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const TableSummary = ({ experiment }: TableSummaryProps) => {
  const { application } = useConfig();

  return (
    <Table striped bordered data-testid="table-summary" className="mb-4">
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
        <tr>
          <th>Risk mitigation checklist</th>
          <td data-testid="experiment-risk-mitigation-link">
            {experiment.riskMitigationLink ? (
              <LinkExternal href={experiment.riskMitigationLink}>
                <span className="mr-1 align-middle">
                  {experiment.riskMitigationLink}
                </span>
                <ExternalIcon />
              </LinkExternal>
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
                      {documentationLink.title}
                    </span>
                    <ExternalIcon />
                  </LinkExternal>
                ))}
              </td>
            </tr>
          )}
        {experiment.featureConfig?.name && (
          <tr>
            <th>Feature config</th>
            <td data-testid="experiment-feature-config">
              {experiment.featureConfig.name}
            </td>
          </tr>
        )}
        {experiment.primaryProbeSets?.length !== 0 && (
          <tr>
            <th>Primary probe sets</th>
            <td data-testid="experiment-probe-primary">
              {experiment
                .primaryProbeSets!.map((probeSet) => probeSet?.name)
                .join(", ")}
            </td>
          </tr>
        )}
        {experiment.secondaryProbeSets?.length !== 0 && (
          <tr>
            <th>Secondary probe sets</th>
            <td data-testid="experiment-probe-secondary">
              {experiment
                .secondaryProbeSets!.map((probeSet) => probeSet?.name)
                .join(", ")}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableSummary;
