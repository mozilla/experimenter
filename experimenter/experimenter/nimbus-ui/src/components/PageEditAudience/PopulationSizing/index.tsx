/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SizingTarget } from "@mozilla/nimbus-schemas";
import React from "react";
import { Form } from "react-bootstrap";
import LinkExternal from "src/components/LinkExternal";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { ReactComponent as Info } from "src/images/info.svg";

type PopulationSizingProps = {
  sizingData: SizingTarget;
  totalClients: number;
};

const popSizingHelpMarkdown =
  "Pre-computed sizing is computed with the [auto-sizing](https://github.com/mozilla/auto-sizing) tool. This assumes a power requirement of 0.8 and is based on Application, Channel, Locale, and Country (and is only available for some common combinations of these).";

const PopulationSizing = ({
  sizingData,
  totalClients,
}: PopulationSizingProps) => (
  <>
    <Form.Label className="d-flex align-items-center">
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
    <Form.Label className="d-flex align-items-center">
      {totalClients} total clients for given parameters
    </Form.Label>
    <p>
      {Object.keys(sizingData.sample_sizes).map((powerKey) => {
        const metrics = sizingData.sample_sizes[powerKey]["metrics"];
        // # clients targeted is the same for each metric for a given power/effect
        const targetedClients =
          metrics[Object.keys(metrics)[0]].number_of_clients_targeted;
        const parameters = sizingData.sample_sizes[powerKey]["parameters"];
        return (
          <>
            <Form.Label style={{ fontWeight: 700 }}>
              Effect Size: {parameters.effect_size * 100}%
            </Form.Label>
            <table className="table-visualization-center border">
              <thead>
                <tr>
                  {Object.keys(metrics).map((metricKey) => (
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
                  {Object.keys(metrics).map((metricKey) => (
                    <td className="align-middle" key={`${metricKey}-sizing`}>
                      <div className="text-secondary">Clients per branch</div>
                      {metrics[metricKey].sample_size_per_branch.toFixed(2)} (
                      {metrics[metricKey].population_percent_per_branch.toFixed(
                        2,
                      )}
                      %)
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

export default React.memo(PopulationSizing);
