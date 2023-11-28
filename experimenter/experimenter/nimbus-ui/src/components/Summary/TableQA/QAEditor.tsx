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
// ELISE - todo - might need this Pick?
// export type TakeawaysEditorProps = UseTakeawaysResult &
//   Pick<getConfig_nimbusConfig, "conclusionRecommendations"> & {
//     setShowEditor: (state: boolean) => void;
//   };

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

  // const qaStatusSlugOptions = [
  //   {
  //     label: "Choose a score",
  //     value: "",
  //     description: "Choose a score",
  //   },
  // {
  //   label: NimbusExperimentQAStatusEnum.RED,
  //   value: NimbusExperimentQAStatusEnum.RED,
  //   description: "🔴 RED ",
  // },
  // {
  //   label: NimbusExperimentQAStatusEnum.YELLOW,
  //   value: NimbusExperimentQAStatusEnum.YELLOW,
  //   description: "🟡 YELLOW ",
  // },
  // {
  //   label: NimbusExperimentQAStatusEnum.GREEN,
  //   value: NimbusExperimentQAStatusEnum.GREEN,
  //   description: "🟢 GREEN ",
  // },
  // ];

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
    <section id="qa-editor" data-testid="QAEditor">
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

          <Form.Group as={Row} controlId="qaStatus" className="mb-0 pl-1">
            {/* <Form.Group data-testid="qa-status" className="ml-3">
              <Form.Control
                as="select"
                onSubmit={handleSave}
                onChange={(e) => setQaStatus(qaStatusField)}
                id="qaStatus"
                {...{ "data-testid": "qaStatus" }}
              >
                <QaStatusSelectOptions options={qaStatusSlugOptions} />
              </Form.Control>
            </Form.Group> */}
            Hello world
          </Form.Group>
        </Form>
      </FormProvider>
    </section>
  );
};

// const QaStatusSelectOptions = ({
//   options,
// }: {
//   options:
//     | null
//     | (null | {
//         label: null | string;
//         value: null | string;
//         description: null | string;
//       })[];
// }) => (
//   <>
//     {options?.map(
//       (item, idx) =>
//         item && (
//           <option key={idx} value={item.value || ""}>
//             `${item.description}`
//           </option>
//         ),
//     )}
//   </>
// );

export default QAEditor;
