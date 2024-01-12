/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { Button, Card, Col, Row, Table } from "react-bootstrap";
import NotSet from "src/components/NotSet";
import QAEditor from "src/components/Summary/TableQA/QAEditor";
import { UseQAResult } from "src/components/Summary/TableQA/useQA";
import { QA_STATUS_PROPERTIES } from "src/lib/constants";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentQAStatusEnum,
} from "src/types/globalTypes";

type TableQAProps = {
  publishStatus: NimbusExperimentPublishStatusEnum | null;
  qaStatus: NimbusExperimentQAStatusEnum | null;
  qaComment?: string | null;
} & UseQAResult;

export type QAEditorProps = UseQAResult & {
  setShowEditor: (state: boolean) => void;
};

const TableQA = (props: TableQAProps) => {
  const { publishStatus, qaStatus, qaComment, showEditor, setShowEditor } =
    props;

  const onClickEdit = useCallback(() => setShowEditor(true), [setShowEditor]);

  if (showEditor) {
    return <QAEditor {...{ ...props, setShowEditor }} />;
  }

  return (
    <Card className="my-4 border-left-0 border-right-0">
      <section id="section-qa" data-testid="section-qa">
        <Card.Header as="h5">
          <Row>
            <Col className="my-1">QA</Col>
            <Col className="text-right">
              {publishStatus !== NimbusExperimentPublishStatusEnum.REVIEW && (
                <Button
                  onClick={onClickEdit}
                  variant="outline-primary"
                  size="sm"
                  className="mx-1"
                  data-testid="edit-qa-status"
                >
                  Edit
                </Button>
              )}
            </Col>
          </Row>
        </Card.Header>
        <Card.Body className=" pe-2 ps-2">
          <Table
            data-testid="table-qa-status"
            style={{ tableLayout: "fixed", whiteSpace: "normal" }}
          >
            <tbody>
              <tr className="w-25">
                <th className="border-top-0 border-bottom-2" colSpan={3}>
                  QA Status
                </th>
                <td
                  data-testid="experiment-qa-status"
                  colSpan={4}
                  className="border-top-0 border-bottom-2"
                >
                  {qaStatus &&
                  qaStatus !== NimbusExperimentQAStatusEnum.NOT_SET ? (
                    QA_STATUS_PROPERTIES[qaStatus].description
                  ) : (
                    <NotSet />
                  )}
                </td>
                <th className="border-top-0 w-75 border-bottom-2"></th>
                <td className="border-top-0 border-bottom-2" />
              </tr>
              {qaComment && (
                <tr>
                  <td
                    colSpan={8}
                    data-testid="qa-comment"
                    className="w-75 border-top-0 border-bottom-2 mr-8"
                    style={{ whiteSpace: "pre-wrap", wordWrap: "normal" }}
                  >
                    {qaComment}
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </Card.Body>
      </section>
    </Card>
  );
};

export default TableQA;
