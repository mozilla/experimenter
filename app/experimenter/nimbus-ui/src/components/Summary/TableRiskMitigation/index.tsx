/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Card, Table } from "react-bootstrap";
import { useConfig, useOutcomes } from "../../../hooks";
import { RISK_QUESTIONS } from "../../../lib/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import NotSet from "../../NotSet";

type TableRiskMitigationProps = {
  experiment: getExperiment_experimentBySlug;
};

// `<tr>`s showing optional fields that are not set are not displayed.

const getRiskLabel = (answer: boolean) =>
  answer ? <span className="font-weight-bold text-danger">Yes</span> : "No";

const TableRiskMitigation = ({ experiment }: TableRiskMitigationProps) => {
  const { applications } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);

  return (
    <Card className="mb-4 border-left-0 border-right-0 border-bottom-0">
      <Card.Header as="h5">Risk Mitigation Questions</Card.Header>
      <Card.Body>
        <Table data-testid="table-risk-mitigation">
          <tbody>
            <tr>
              <th className="border-top-0"> {RISK_QUESTIONS.BRAND}</th>
              <td
                className="border-top-0"
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-1"
              >
                {experiment.riskBrand !== null ? (
                  getRiskLabel(experiment.riskBrand)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th>{RISK_QUESTIONS.REVENUE}</th>
              <td
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-2"
              >
                {experiment.riskRevenue !== null ? (
                  getRiskLabel(experiment.riskRevenue)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
            <tr>
              <th> {RISK_QUESTIONS.PARTNER}</th>
              <td
                colSpan={3}
                data-testid="experiment-risk-mitigation-question-3"
              >
                {experiment.riskPartnerRelated !== null ? (
                  getRiskLabel(experiment.riskPartnerRelated)
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableRiskMitigation;
