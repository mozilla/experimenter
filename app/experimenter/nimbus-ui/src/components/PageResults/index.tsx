/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebarAndData from "../AppLayoutWithSidebarAndData";
import { useAnalysis } from "../../hooks";
import { Alert } from "react-bootstrap";
import LinkExternal from "../LinkExternal";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { slug } = useParams();
  const { loading, error, result } = useAnalysis(slug);

  return (
    <AppLayoutWithSidebarAndData title="Results" testId="PageResults">
      {({ experiment }) => (
        <>
          <p>
            <b>Analysis data for &quot;{experiment.name}&quot;</b>
          </p>
          {loading ? (
            <p data-testid="analysis-loading">Loading data...</p>
          ) : (
            <>
              {error && (
                <Alert data-testid="analysis-error" variant="warning">
                  Could not load experiment analysis data. Please contact data
                  science in{" "}
                  <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
                    #cirrus
                  </LinkExternal>{" "}
                  about this.
                </Alert>
              )}
              {result && (
                <p data-testid="analysis-data">
                  Data: {JSON.stringify(result)}
                </p>
              )}
            </>
          )}
        </>
      )}
    </AppLayoutWithSidebarAndData>
  );
};

export default PageResults;
