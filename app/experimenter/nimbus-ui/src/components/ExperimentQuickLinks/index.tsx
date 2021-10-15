/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { ListGroup } from "react-bootstrap";
import { useAnalysis, useConfig } from "../../hooks";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";
import {
  BASE_PATH,
  EXTERNAL_URLS,
  TOOLTIP_LIVE_MONITORING,
} from "../../lib/constants";
import { StatusCheck } from "../../lib/experiment";
import { analysisUnavailable } from "../../lib/visualization/utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import LinkExternal from "../LinkExternal";
import "./index.scss";

export const ExperimentQuickLinks = ({
  slug,
  documentationLinks,
  monitoringDashboardUrl,
  recipeJson,
  status,
}: Pick<
  getExperiment_experimentBySlug,
  "slug" | "documentationLinks" | "monitoringDashboardUrl" | "recipeJson"
> & {
  status: StatusCheck;
}) => {
  const { documentationLink: configDocumentationLinks } = useConfig();
  const { result: analysis } = useAnalysis();
  const slugUnderscored = slug.replace(/-/g, "_");

  return (
    <ListGroup horizontal className="experiment-quick-links">
      {documentationLinks &&
        documentationLinks?.length > 0 &&
        documentationLinks.map((documentationLink, idx) => (
          <ListGroup.Item key={idx}>
            <LinkExternal
              href={documentationLink.link}
              data-testid="experiment-additional-link"
              key={`doc-link-${idx}`}
              className="d-block"
            >
              {
                configDocumentationLinks!.find(
                  (d) => d?.value === documentationLink.title,
                )?.label
              }
              &nbsp;
              <ExternalIcon />
            </LinkExternal>
          </ListGroup.Item>
        ))}

      {status.launched && (
        <ListGroup.Item>
          <LinkExternal
            href={monitoringDashboardUrl!}
            title={TOOLTIP_LIVE_MONITORING}
            data-testid="experiment-quick-link-monitoring-dashboard"
          >
            Live Monitoring Dashboard&nbsp;
            <ExternalIcon />
          </LinkExternal>
        </ListGroup.Item>
      )}

      {status.launched && !analysisUnavailable(analysis) && (
        <ListGroup.Item>
          <LinkExternal
            href={EXTERNAL_URLS.DETAILED_ANALYSIS_TEMPLATE(slugUnderscored)}
            data-testid="link-external-results"
          >
            Detailed Analysis&nbsp;
            <ExternalIcon />
          </LinkExternal>
        </ListGroup.Item>
      )}

      {recipeJson && (
        <ListGroup.Item>
          <a href={`${BASE_PATH}/${slug}/details#recipe-json`}>
            Preview Recipe JSON
          </a>
        </ListGroup.Item>
      )}
    </ListGroup>
  );
};

export default ExperimentQuickLinks;
