/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SizingByUserType } from "@mozilla/nimbus-schemas";
import React from "react";
import { Form } from "react-bootstrap";
import { Code } from "src/components/Code";
import LinkExternal from "src/components/LinkExternal";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { ReactComponent as Info } from "src/images/info.svg";

type PopulationSizingProps = {
  sizingData: SizingByUserType;
  totalNewClients: number;
  totalExistingClients: number;
};

const popSizingHelpMarkdown =
  "Pre-computed sizing is computed with the [auto-sizing](https://github.com/mozilla/auto-sizing) tool. This assumes a power requirement of 0.8 and is based on Application, Channel, Locale (or Language), and Country (and is only available for some common combinations of these).";

const PopulationSizing = ({
  sizingData,
  totalNewClients,
  totalExistingClients,
}: PopulationSizingProps) => {
  const newUserSizing = sizingData.new;
  const existingUserSizing = sizingData.existing;
  const targetingParameters = JSON.stringify(
    newUserSizing.target_recipe,
    (k, v) => (k === "new_or_existing" ? undefined : v),
  );
  return (
    <>
      <Form.Label
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
        <Form.Label className="d-flex align-items-center">
          Targeting Parameters
        </Form.Label>
        <Code codeString={targetingParameters} />
      </Form.Group>
      <Form.Label
        className="d-flex align-items-center"
        data-testid="new-total-clients-label"
      >
        {totalNewClients} total{" "}
        <span
          style={{ fontWeight: 700, marginLeft: "0.3em", marginRight: "0.3em" }}
        >
          new
        </span>{" "}
        clients for given parameters
      </Form.Label>
      <Form.Label
        className="d-flex align-items-center"
        data-testid="existing-total-clients-label"
      >
        {totalExistingClients} total{" "}
        <span
          style={{ fontWeight: 700, marginLeft: "0.3em", marginRight: "0.3em" }}
        >
          existing
        </span>{" "}
        clients for given parameters
      </Form.Label>
      <p>
        {Object.keys(newUserSizing.sample_sizes).map((powerKey) => {
          // powerKey is the same for new and existing so we can look both up with the same key
          const newUserMetrics =
            newUserSizing.sample_sizes[powerKey]["metrics"];
          const existingUserMetrics =
            existingUserSizing.sample_sizes[powerKey]["metrics"];
          // parameters are the same for new and existing so we only need to get one
          const parameters = newUserSizing.sample_sizes[powerKey]["parameters"];
          return (
            <>
              <Form.Label style={{ fontWeight: 700 }}>
                Effect Size: {parameters.effect_size * 100}%
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
                        <table
                          className="table-visualization-center-no-border"
                          style={{ padding: 0, margin: 0 }}
                        >
                          <tbody>
                            <tr>
                              <td
                                style={{
                                  textAlign: "end",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <span className="text-secondary">
                                  Percent of clients:{" "}
                                </span>
                              </td>
                              <td
                                style={{
                                  textAlign: "start",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <b>
                                  {newUserMetrics[
                                    metricKey
                                  ].population_percent_per_branch.toFixed(2)}
                                  %
                                </b>
                                <span className="text-secondary">
                                  {" "}
                                  (per branch)
                                </span>
                              </td>
                            </tr>
                            <tr>
                              <td
                                style={{
                                  textAlign: "end",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <span className="text-secondary">
                                  Expected number of clients:{" "}
                                </span>
                              </td>
                              <td
                                style={{
                                  textAlign: "start",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <b>
                                  {newUserMetrics[
                                    metricKey
                                  ].sample_size_per_branch.toFixed(2)}
                                </b>
                                <span className="text-secondary">
                                  {" "}
                                  (per branch)
                                </span>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </td>
                    ))}
                  </tr>
                  <tr key={`${powerKey}-metrics`}>
                    <th className="align-middle" scope="row">
                      Existing Clients
                    </th>
                    {Object.keys(existingUserMetrics).map((metricKey) => (
                      <td className="align-middle" key={`${metricKey}-sizing`}>
                        <table
                          className="table-visualization-center-no-border"
                          style={{ padding: 0, margin: 0 }}
                        >
                          <tbody>
                            <tr>
                              <td
                                style={{
                                  textAlign: "end",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <span className="text-secondary">
                                  Percent of clients:{" "}
                                </span>
                              </td>
                              <td
                                style={{
                                  textAlign: "start",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <b>
                                  {existingUserMetrics[
                                    metricKey
                                  ].population_percent_per_branch.toFixed(2)}
                                  %
                                </b>
                                <span className="text-secondary">
                                  {" "}
                                  (per branch)
                                </span>
                              </td>
                            </tr>
                            <tr>
                              <td
                                style={{
                                  textAlign: "end",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <span className="text-secondary">
                                  Expected number of clients:{" "}
                                </span>
                              </td>
                              <td
                                style={{
                                  textAlign: "start",
                                  border: "none",
                                  padding: "0.25rem",
                                }}
                              >
                                <b>
                                  {existingUserMetrics[
                                    metricKey
                                  ].sample_size_per_branch.toFixed(2)}
                                </b>
                                <span className="text-secondary">
                                  {" "}
                                  (per branch)
                                </span>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </>
          );
        })}
      </p>
    </>
  );
};

export default React.memo(PopulationSizing);
