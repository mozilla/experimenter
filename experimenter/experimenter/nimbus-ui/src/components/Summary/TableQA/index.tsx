/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { Button, Card, Col, Row, Table } from "react-bootstrap";
import NotSet from "src/components/NotSet";
import QAEditor from "src/components/Summary/TableQA/QAEditor";
import { UseQAResult } from "src/components/Summary/TableQA/useQA";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

type TableQAProps = {
  qaStatus?: NimbusExperimentQAStatusEnum | null;
} & UseQAResult;

export type QAEditorProps = UseQAResult & {
  setShowEditor: (state: boolean) => void;
};

const TableQA = (props: TableQAProps) => {
  const { qaStatus, showEditor, setShowEditor } = props;

  const onClickEdit = useCallback(() => setShowEditor(true), [setShowEditor]);

  if (showEditor) {
    return <QAEditor {...{ ...props, setShowEditor }} />;
  }

  return (
    <Card className="my-4 border-left-0 border-right-0">
      <Card.Header as="h5">
        <Row>
          <Col className="my-1">QA</Col>
          <Col className="text-right">
            {
              <Button
                onClick={onClickEdit}
                variant="outline-primary"
                size="sm"
                className="mx-1"
                data-testid="edit-qa-status"
              >
                Edit
              </Button>
            }
          </Col>
        </Row>
      </Card.Header>
      <Card.Body className=" pe-2 ps-2">
        <Table data-testid="table-qa-status">
          <tbody>
            <tr className="w-25">
              <th className="border-top-0 border-bottom-2">QA Status</th>
              <td
                data-testid="experiment-qa-status"
                className="text-monospace border-top-0 border-bottom-2"
              >
                {qaStatus || <NotSet />}
              </td>
              <th className="border-top-0 w-75 border-bottom-2"></th>
              <td className="border-top-0 border-bottom-2" />
            </tr>
          </tbody>
        </Table>
      </Card.Body>
    </Card>
  );
};

export default TableQA;
