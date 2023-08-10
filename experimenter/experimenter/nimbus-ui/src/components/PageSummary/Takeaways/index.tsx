/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { Card, Table } from "react-bootstrap";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import ReactMarkdown from "react-markdown";
import NotSet from "src/components/NotSet";
import TakeawaysEditor from "src/components/PageSummary/Takeaways/TakeawaysEditor";
import { UseTakeawaysResult } from "src/components/PageSummary/Takeaways/useTakeaways";
import { useConfig } from "src/hooks";

export * from "./useTakeaways";

export type TakeawaysProps = UseTakeawaysResult;

export const Takeaways = (props: TakeawaysProps) => {
  const {
    showEditor,
    setShowEditor,
    conclusionRecommendation,
    takeawaysSummary,
    takeawaysQbrLearning,
    takeawaysMetricGain,
    takeawaysGainAmount,
    isArchived,
  } = props;

  const { conclusionRecommendations } = useConfig();
  const onClickEdit = useCallback(() => setShowEditor(true), [setShowEditor]);

  if (showEditor) {
    return (
      <TakeawaysEditor
        {...{ ...props, conclusionRecommendations, setShowEditor }}
      />
    );
  }

  const conclusionRecommendationLabel = conclusionRecommendations?.find(
    (item) => item!.value === conclusionRecommendation,
  )?.label;

  const setTextColor = (field: boolean | null) => {
    return field ? "text-success font-weight-bold" : "text-body";
  };

  return (
    <Card className="border-left-0 border-right-0 border-bottom-0 my-4">
      <section id="takeaways" data-testid="Takeaways">
        <Card.Header as="h5">
          <Row>
            <Col className="my-1">
              Takeaways
              {conclusionRecommendationLabel && (
                <Badge
                  className="ml-2 border rounded-pill px-2 bg-white border-primary text-primary font-weight-normal"
                  data-testid="conclusion-recommendation-status"
                >
                  {conclusionRecommendationLabel}
                </Badge>
              )}
            </Col>
            <Col className="text-right">
              {!isArchived && (
                <Button
                  onClick={onClickEdit}
                  variant="outline-primary"
                  size="sm"
                  className="mx-1"
                  data-testid="edit-takeaways"
                >
                  Edit
                </Button>
              )}
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Table data-testid="table-takeaway-summary">
            <tr data-testid="qbr-learning">
              <th className="border-top-0 mr-3">QBR Learning</th>
              <td className="border-top-0 table-fixed col-sm-4 col-md-4 align-items-start justify-content-start">
                <span className={setTextColor(takeawaysQbrLearning)}>
                  {takeawaysQbrLearning ? "True" : "False"}
                </span>
              </td>
              <th className="border-top-0 mr-2">
                Statistically Significant DAU Gain
              </th>
              <td className="border-top-0 table-fixed col-sm-3 col-md-3">
                <span className={setTextColor(takeawaysMetricGain)}>
                  {takeawaysMetricGain ? "True" : "False"}
                </span>
              </td>
            </tr>

            <tr data-testid="summary">
              <th className="mr-auto col-sm-2">Summary</th>
              <td colSpan={3}>
                {takeawaysSummary ? (
                  <div data-testid="takeaways-summary-rendered">
                    <ReactMarkdown>{takeawaysSummary}</ReactMarkdown>
                  </div>
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>

            <tr data-testid="gain-amount">
              <th>Gain Amount</th>
              <td colSpan={3}>
                {takeawaysGainAmount ? (
                  <div data-testid="takeaways-gain-amount-rendered">
                    <ReactMarkdown>{takeawaysGainAmount}</ReactMarkdown>
                  </div>
                ) : (
                  <NotSet />
                )}
              </td>
            </tr>
          </Table>
        </Card.Body>
      </section>
    </Card>
  );
};

export default Takeaways;
