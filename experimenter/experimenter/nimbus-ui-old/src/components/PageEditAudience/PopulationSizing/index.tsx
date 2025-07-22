/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SizingByUserType } from "@mozilla/nimbus-schemas";
import React from "react";
import { Form } from "react-bootstrap";
import { Code } from "src/components/Code";
import LinkExternal from "src/components/LinkExternal";
import PopulationSizingCountTable from "src/components/PageEditAudience/PopulationSizing/PopulationSizingCountTable";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { ReactComponent as Info } from "src/images/info.svg";

type PopulationSizingProps = {
  sizingData: SizingByUserType;
  totalNewClients: number;
  totalExistingClients: number;
  totalClients: number;
};

const popSizingHelpMarkdown =
  "Pre-computed sizing is computed with the [auto-sizing](https://github.com/mozilla/auto-sizing) tool. This assumes a power requirement of 0.8 and is based on Application, Channel, Locale (or Language), and Country (and is only available for some common combinations of these).";

const newClientsHelpMarkdown =
  "'**New**' is the # of clients *first seen* during the 7-day enrollment period of the simulated experiment.";
const existingClientsHelpMarkdown =
  "'**Existing**' is the # of clients *active* during during the 7-day enrollment period of the simulated experiment, who were first seen *more than 28 days prior* to the start of the enrollment period.";
const allClientsHelpMarkdown =
  "'**Total**' is the # of clients *active* during the 7-day enrollment period of the simulated experiment, regardless of first seen date.";

const PopulationSizing = ({
  sizingData,
  totalNewClients,
  totalExistingClients,
  totalClients,
}: PopulationSizingProps) => {
  const newUserSizing = sizingData.new;
  const existingUserSizing = sizingData.existing;
  const allUserSizing = sizingData.all;
  const targetingParameters = JSON.stringify(
    newUserSizing.target_recipe,
    (k, v) => (k === "new_or_existing" ? undefined : v),
  );
  return (
    <>
      <Form.Label
        as="h5"
        className="d-flex align-items-center"
        data-testid="population-sizing-precomputed-values"
      >
        Pre-computed population sizing data
        <Info
          data-tip
          data-for="auto-sizing-help"
          width="20"
          height="20"
          className="ml-1"
        />
        <TooltipWithMarkdown
          tooltipId="auto-sizing-help"
          markdown={popSizingHelpMarkdown}
        />
      </Form.Label>
      <div>
        <p className="text-secondary">
          This is meant as a guide for certain targeting parameters. As always,
          contact Data Science in{" "}
          <LinkExternal href="https://mozilla.slack.com/archives/CF94YGE03">
            #ask-experimenter
          </LinkExternal>{" "}
          for assistance.
        </p>
      </div>
      <Form.Group>
        <Form.Label as="h6" className="d-flex align-items-center">
          <strong>Targeting Parameters</strong>
        </Form.Label>
        <Code codeString={targetingParameters} />
      </Form.Group>
      <Form.Label as="h6" className="d-flex align-items-center">
        <strong>Client counts for these targeting parameters</strong>
      </Form.Label>
      <p className="text-secondary">
        Pre-computed sizing information is computed using a simulated experiment
        with a 7 day enrollment period and 28 day observation period.
      </p>
      <div className="ml-4 mb-4">
        <Form.Label
          className="d-flex align-items-center"
          data-testid="new-total-clients-label"
        >
          {totalNewClients} new clients
          <Info
            data-tip
            data-for="auto-sizing-help-new-clients"
            width="20"
            height="20"
            className="ml-1 mr-1"
          />
          <TooltipWithMarkdown
            tooltipId="auto-sizing-help-new-clients"
            markdown={newClientsHelpMarkdown}
          />
        </Form.Label>
        <Form.Label
          className="d-flex align-items-center"
          data-testid="existing-total-clients-label"
        >
          {totalExistingClients} existing clients
          <Info
            data-tip
            data-for="auto-sizing-help-existing-clients"
            width="20"
            height="20"
            className="ml-1 mr-1"
          />
          <TooltipWithMarkdown
            tooltipId="auto-sizing-help-existing-clients"
            markdown={existingClientsHelpMarkdown}
          />
        </Form.Label>
        <Form.Label
          className="d-flex align-items-center"
          data-testid="all-total-clients-label"
        >
          {totalClients} total clients
          <Info
            data-tip
            data-for="auto-sizing-help-all-clients"
            width="20"
            height="20"
            className="ml-1 mr-1"
          />
          <TooltipWithMarkdown
            tooltipId="auto-sizing-help-all-clients"
            markdown={allClientsHelpMarkdown}
          />
        </Form.Label>
      </div>
      <div>
        {Object.keys(newUserSizing.sample_sizes).map((powerKey) => {
          // powerKey is the same for new and existing so we can look both up with the same key
          const newUserMetrics =
            newUserSizing.sample_sizes[powerKey]["metrics"];
          const existingUserMetrics =
            existingUserSizing.sample_sizes[powerKey]["metrics"];
          const allUserMetrics =
            allUserSizing.sample_sizes[powerKey]["metrics"];
          // parameters are the same for new and existing so we only need to get one
          const parameters = newUserSizing.sample_sizes[powerKey]["parameters"];
          return (
            <>
              <Form.Label>
                Effect Size:&nbsp;
                <strong>{(parameters.effect_size * 100).toFixed(2)}%</strong>
              </Form.Label>
              <table className="table-visualization-center border">
                <thead>
                  <tr>
                    <th scope="col" className="border-bottom-0 bg-light" />
                    {Object.keys(newUserMetrics).map((metricKey) => (
                      <th
                        key={metricKey}
                        className="border-bottom-0 bg-light"
                        scope="col"
                      >
                        <div>{metricKey}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr key={`${powerKey}-metrics`}>
                    <th className="align-middle" scope="row">
                      New Clients
                    </th>
                    {Object.keys(newUserMetrics).map((metricKey) => (
                      <td className="align-middle" key={`${metricKey}-sizing`}>
                        <PopulationSizingCountTable
                          percent={
                            newUserMetrics[metricKey]
                              .population_percent_per_branch
                          }
                          count={
                            newUserMetrics[metricKey].sample_size_per_branch
                          }
                        />
                      </td>
                    ))}
                  </tr>
                  <tr key={`${powerKey}-metrics`}>
                    <th className="align-middle" scope="row">
                      Existing Clients
                    </th>
                    {Object.keys(existingUserMetrics).map((metricKey) => (
                      <td className="align-middle" key={`${metricKey}-sizing`}>
                        <PopulationSizingCountTable
                          percent={
                            existingUserMetrics[metricKey]
                              .population_percent_per_branch
                          }
                          count={
                            existingUserMetrics[metricKey]
                              .sample_size_per_branch
                          }
                        />
                      </td>
                    ))}
                  </tr>
                  <tr key={`${powerKey}-metrics`}>
                    <th className="align-middle" scope="row">
                      All Clients
                    </th>
                    {Object.keys(allUserMetrics).map((metricKey) => (
                      <td className="align-middle" key={`${metricKey}-sizing`}>
                        <PopulationSizingCountTable
                          percent={
                            allUserMetrics[metricKey]
                              .population_percent_per_branch
                          }
                          count={
                            allUserMetrics[metricKey].sample_size_per_branch
                          }
                        />
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </>
          );
        })}
      </div>
    </>
  );
};

export default React.memo(PopulationSizing);
