/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useCallback } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FormProvider } from "react-hook-form";
import { useCommonForm } from "../../../hooks";
import { getConfig_nimbusConfig } from "../../../types/getConfig";
import { UseTakeawaysResult } from "./useTakeaways";

export const takeawaysEditorFieldNames = [
  "conclusionRecommendation",
  "takeawaysSummary",
] as const;

type TakeawaysEditorFieldName = typeof takeawaysEditorFieldNames[number];

export type TakeawaysEditorProps = UseTakeawaysResult &
  Pick<getConfig_nimbusConfig, "conclusionRecommendations"> & {
    setShowEditor: (state: boolean) => void;
  };

export const TakeawaysEditor = ({
  isLoading,
  conclusionRecommendations,
  conclusionRecommendation,
  takeawaysSummary,
  setShowEditor,
  onSubmit,
  submitErrors,
  setSubmitErrors,
  isServerValid,
}: TakeawaysEditorProps) => {
  const defaultValues = { conclusionRecommendation, takeawaysSummary };
  type DefaultValues = typeof defaultValues;

  const {
    isValid,
    isSubmitted,
    FormErrors,
    formControlAttrs,
    handleSubmit,
    formMethods,
  } = useCommonForm<TakeawaysEditorFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
    {},
  );

  const onClickCancel = useCallback(
    () => setShowEditor(false),
    [setShowEditor],
  );

  const handleSave = handleSubmit(async (data: DefaultValues) => {
    if (isLoading) return;
    await onSubmit(data);
  });

  const conclusionRadioAttrs = formControlAttrs(
    "conclusionRecommendation",
    {},
    false,
  );

  return (
    <section id="takeaways-editor" data-testid="TakeawaysEditor">
      <h3 className="h4 mb-3 mt-4">
        <Row>
          <Col>Takeaways</Col>
          <Col className="text-right">
            <Button
              onClick={handleSave}
              disabled={isLoading}
              variant="primary"
              size="sm"
              className="mx-1"
            >
              Save
            </Button>
            <Button
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
          data-testid="FormTakeaways"
        >
          {submitErrors["*"] && (
            <Alert data-testid="submit-error" variant="warning">
              {submitErrors["*"]}
            </Alert>
          )}
          <Form.Group as={Row}>
            <Form.Group
              as={Col}
              className="flex-grow-0"
              controlId="conclusionRecommendation"
            >
              <Form.Label
                className={classNames("font-weight-bold", {
                  "is-invalid": !!submitErrors["conclusion_recommendation"],
                })}
              >
                Recommendation:
              </Form.Label>
              {conclusionRecommendations!.map((option, idx) => (
                <Form.Check
                  key={idx}
                  type="radio"
                  value={option!.value!}
                  label={option!.label!}
                  title={option!.label!}
                  {...conclusionRadioAttrs}
                  id={`conclusionRecommendation-${option!.value!}}`}
                />
              ))}
              <FormErrors name="conclusionRecommendation" />
            </Form.Group>
            <Form.Group as={Col} controlId="takeawaysSummary">
              <Form.Label className="font-weight-bold">Summary:</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                {...formControlAttrs("takeawaysSummary")}
              />
              <FormErrors name="takeawaysSummary" />
            </Form.Group>
          </Form.Group>
        </Form>
      </FormProvider>
    </section>
  );
};

export default TakeawaysEditor;
