/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FormProvider } from "react-hook-form";
import { UseQAResult } from "src/components/Summary/TableQA/useQA";
import { useCommonForm } from "src/hooks";
import { QA_STATUS_PROPERTIES } from "src/lib/constants";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

export const qaEditorFieldNames = ["qaStatus", "qaComment"] as const;

type QAEditorFieldName = typeof qaEditorFieldNames[number];

export type QAEditorProps = UseQAResult & {
  setShowEditor: (state: boolean) => void;
};

export const QAEditor = ({
  isLoading,
  qaStatus,
  qaComment,
  setShowEditor,
  onSubmit,
  submitErrors,
  setSubmitErrors,
  isServerValid,
}: QAEditorProps) => {
  const defaultValues = {
    qaStatus,
    qaComment,
  };

  type DefaultValues = typeof defaultValues;

  const {
    isValid,
    isSubmitted,
    FormErrors,
    formControlAttrs,
    handleSubmit,
    formMethods,
  } = useCommonForm<QAEditorFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
    {},
  );

  const qaStatusOptions = [
    {
      label: NimbusExperimentQAStatusEnum.NOT_SET,
      value: NimbusExperimentQAStatusEnum.NOT_SET,
      description:
        QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.NOT_SET].description,
    },
    {
      label: NimbusExperimentQAStatusEnum.RED,
      value: NimbusExperimentQAStatusEnum.RED,
      description:
        QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.RED].description,
    },
    {
      label: NimbusExperimentQAStatusEnum.YELLOW,
      value: NimbusExperimentQAStatusEnum.YELLOW,
      description:
        QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.YELLOW].description,
    },
    {
      label: NimbusExperimentQAStatusEnum.GREEN,
      value: NimbusExperimentQAStatusEnum.GREEN,
      description:
        QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
    },
  ] as const;

  const onClickCancel = useCallback(
    () => setShowEditor(false),
    [setShowEditor],
  );

  const [qaStatusField, setQaStatus] =
    useState<NimbusExperimentQAStatusEnum | null>(qaStatus);

  const handleSave = handleSubmit(async (data: DefaultValues) => {
    if (isLoading) return;
    data.qaStatus = qaStatusField;
    await onSubmit(data);
  });

  return (
    <section id="qa-editor" className="mx-4" data-testid="QAEditor">
      <h3 className="h4 mb-3 mt-4">
        <Row>
          <Col>QA</Col>
          <Col className="text-right">
            <Button
              data-testid="qa-edit-save"
              onClick={handleSave}
              disabled={isLoading}
              variant="primary"
              size="sm"
              className="mx-1"
            >
              Save
            </Button>
            <Button
              data-testid="qa-edit-cancel"
              onClick={onClickCancel}
              disabled={isLoading}
              variant="secondary"
              size="sm"
              className="mx-1"
            >
              Cancel
            </Button>
          </Col>
        </Row>
      </h3>
      <FormProvider {...formMethods}>
        <Form
          noValidate
          onSubmit={handleSave}
          validated={isSubmitted && isValid}
          data-testid="FormQA"
        >
          {submitErrors["*"] && (
            <Alert data-testid="submit-error" variant="warning">
              {submitErrors["*"]}
            </Alert>
          )}

          <Form.Group
            as={Row}
            data-testid="qa-status-section"
            className="mb-0 pl-3"
          >
            <Col className="mr-0 pl-0 pr-0 w-25">
              <Form.Label>
                <p className="font-weight-bold">QA Status: </p>
              </Form.Label>
            </Col>
            <Col className="flex-fill pl-0 pr-8 mr-4">
              <Form.Control
                as="select"
                className="ml-0 mr-0"
                value={qaStatusField as NimbusExperimentQAStatusEnum}
                onSubmit={handleSave}
                onChange={(e) =>
                  setQaStatus(
                    e.target
                      ? (e.target.value as NimbusExperimentQAStatusEnum)
                      : NimbusExperimentQAStatusEnum.NOT_SET,
                  )
                }
                id="qa-status-select"
                data-testid="qa-status"
              >
                {qaStatusOptions.map(
                  (item, idx) =>
                    item && (
                      <option key={idx} value={item.value}>
                        {item.description}
                      </option>
                    ),
                )}
              </Form.Control>
            </Col>
          </Form.Group>
          <Form.Group
            as={Row}
            data-testid="qa-comment-section"
            className="mt-4 pl-3"
          >
            <Form.Label className="font-weight-bold">Comment:</Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              {...formControlAttrs("qaComment")}
              className="pr-8 mr-4"
            />
            <FormErrors name="qaComment" />
          </Form.Group>
        </Form>
      </FormProvider>
    </section>
  );
};

export default QAEditor;
