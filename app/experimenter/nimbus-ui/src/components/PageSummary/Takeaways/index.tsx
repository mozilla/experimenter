/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import ReactMarkdown from "react-markdown";
import { useConfig } from "../../../hooks";
import NotSet from "../../NotSet";
import TakeawaysEditor from "./TakeawaysEditor";
import { UseTakeawaysResult } from "./useTakeaways";

export * from "./useTakeaways";

export type TakeawaysProps = UseTakeawaysResult;

export const Takeaways = (props: TakeawaysProps) => {
  const {
    showEditor,
    setShowEditor,
    conclusionRecommendation,
    takeawaysSummary,
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

  return (
    <section id="takeaways" data-testid="Takeaways">
      <h3 className="h4 mb-3 mt-4">
        <Row>
          <Col>
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
      </h3>
      {takeawaysSummary ? (
        <div data-testid="takeaways-summary-rendered">
          <ReactMarkdown source={takeawaysSummary} />
        </div>
      ) : (
        <NotSet />
      )}
    </section>
  );
};

export default Takeaways;
