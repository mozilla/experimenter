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
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

export const qaEditorFieldNames = ["qaStatus"] as const;

type QAEditorFieldName = typeof qaEditorFieldNames[number];

export type QAEditorProps = UseQAResult & {
  setShowEditor: (state: boolean) => void;
};

export const QAEditor = ({
  isLoading,
  qaStatus,
  setShowEditor,
  onSubmit,
  submitErrors,
  setSubmitErrors,
  isServerValid,
}: QAEditorProps) => {
  const defaultValues = {
    qaStatus,
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
      label: "Choose a score",
      value: "",
      description: "Choose a score",
    },
    {
      label: NimbusExperimentQAStatusEnum.RED,
      value: NimbusExperimentQAStatusEnum.RED,
      description: NimbusExperimentQAStatusEnum.RED,
    },
    {
      label: NimbusExperimentQAStatusEnum.YELLOW,
      value: NimbusExperimentQAStatusEnum.YELLOW,
      description: NimbusExperimentQAStatusEnum.YELLOW,
    },
    {
      label: NimbusExperimentQAStatusEnum.GREEN,
      value: NimbusExperimentQAStatusEnum.GREEN,
      description: NimbusExperimentQAStatusEnum.GREEN,
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

          <Form.Group as={Row} className="mb-0 pl-1">
            <Row className="ml-0 flex-fill pl-0">
              <Col className="ml-2 mr-0 pr-0 w-25">
                <Form.Label>
                  <p className="font-weight-bold">QA Status: </p>
                </Form.Label>
              </Col>
              <Col className="ml-4 flex-fill pl-0 pr-8 mr-4">
                <Form.Control
                  as="select"
                  className="ml-0 mr-0"
                  value={qaStatusField as NimbusExperimentQAStatusEnum}
                  onSubmit={handleSave}
                  onChange={(e) =>
                    setQaStatus(
                      e.target
                        ? (e.target.value as NimbusExperimentQAStatusEnum)
                        : null,
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
            </Row>
          </Form.Group>
        </Form>
      </FormProvider>
    </section>
  );
};

export default QAEditor;
