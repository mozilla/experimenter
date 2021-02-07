/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { Table } from "react-bootstrap";
import { displayConfigLabelOrNotSet } from "..";
import { useConfig } from "../../../hooks";
import { ReactComponent as ExternalIcon } from "../../../images/external.svg";
import { ExperimentContext } from "../../../lib/contexts";
import LinkExternal from "../../LinkExternal";
import NotSet from "../../NotSet";
import RichText from "../../RichText";

// `<tr>`s showing optional fields that are not set are not displayed.

const TableSummary = () => {
  const { experiment } = useContext(ExperimentContext);
  const {
    slug,
    owner,
    application,
    hypothesis,
    publicDescription,
    riskMitigationLink,
    documentationLinks,
    featureConfig,
    primaryProbeSets,
    secondaryProbeSets,
  } = experiment!;

  const {
    application: configApplications,
    documentationLink: configDocumentationLinks,
  } = useConfig();

  return (
    <Table striped bordered data-testid="table-summary" className="mb-4">
      <tbody>
        <tr>
          <th className="w-33">Slug</th>
          <td data-testid="experiment-slug" className="text-monospace">
            {slug}
          </td>
        </tr>
        <tr>
          <th>Experiment owner</th>
          <td data-testid="experiment-owner">
            {owner ? owner.email : <NotSet />}
          </td>
        </tr>
        <tr>
          <th>Application</th>
          <td data-testid="experiment-application">
            {displayConfigLabelOrNotSet(application, configApplications)}
          </td>
        </tr>
        <tr>
          <th>Hypothesis</th>
          <td data-testid="experiment-hypothesis">
            <RichText text={hypothesis || ""} />
          </td>
        </tr>
        <tr>
          <th>Public description</th>
          <td data-testid="experiment-description">
            {publicDescription ? publicDescription : <NotSet />}
          </td>
        </tr>
        <tr>
          <th>Risk mitigation checklist</th>
          <td data-testid="experiment-risk-mitigation-link">
            {riskMitigationLink ? (
              <LinkExternal href={riskMitigationLink}>
                <span className="mr-1 align-middle">{riskMitigationLink}</span>
                <ExternalIcon />
              </LinkExternal>
            ) : (
              <NotSet />
            )}
          </td>
        </tr>
        {documentationLinks && documentationLinks?.length > 0 && (
          <tr>
            <th>Additional links</th>
            <td data-testid="experiment-additional-links">
              {documentationLinks.map((documentationLink, idx) => (
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
        {featureConfig?.name && (
          <tr>
            <th>Feature config</th>
            <td data-testid="experiment-feature-config">
              {featureConfig.name}
            </td>
          </tr>
        )}
        {primaryProbeSets?.length !== 0 && (
          <tr>
            <th>Primary probe sets</th>
            <td data-testid="experiment-probe-primary">
              {primaryProbeSets!.map((probeSet) => probeSet?.name).join(", ")}
            </td>
          </tr>
        )}
        {secondaryProbeSets?.length !== 0 && (
          <tr>
            <th>Secondary probe sets</th>
            <td data-testid="experiment-probe-secondary">
              {secondaryProbeSets!.map((probeSet) => probeSet?.name).join(", ")}
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableSummary;
