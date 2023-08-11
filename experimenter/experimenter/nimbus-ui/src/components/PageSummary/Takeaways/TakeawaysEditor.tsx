/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FormProvider } from "react-hook-form";
import { UseTakeawaysResult } from "src/components/PageSummary/Takeaways/useTakeaways";
import { useCommonForm } from "src/hooks";
import { getConfig_nimbusConfig } from "src/types/getConfig";

export const takeawaysEditorFieldNames = [
  "conclusionRecommendation",
  "takeawaysSummary",
  "takeawaysQbrLearning",
  "takeawaysMetricGain",
  "takeawaysGainAmount",
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
  takeawaysQbrLearning,
  takeawaysMetricGain,
  takeawaysGainAmount,
  setShowEditor,
  onSubmit,
  submitErrors,
  setSubmitErrors,
  isServerValid,
}: TakeawaysEditorProps) => {
  const defaultValues = {
    conclusionRecommendation,
    takeawaysSummary,
    takeawaysQbrLearning,
    takeawaysMetricGain,
    takeawaysGainAmount,
  };

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

  const [isQbrLearning, setIsQbrLearning] =
    useState<boolean>(takeawaysQbrLearning);

  const [isMetricGain, setIsMetricGain] =
    useState<boolean>(takeawaysMetricGain);

  const handleSave = handleSubmit(async (data: DefaultValues) => {
    if (isLoading) return;
    data.takeawaysQbrLearning = isQbrLearning;
    data.takeawaysMetricGain = isMetricGain;
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
              data-testid="takeaways-edit-save"
              onClick={handleSave}
              disabled={isLoading}
              variant="primary"
              size="sm"
              className="mx-1"
            >
              Save
            </Button>
            <Button
              data-testid="takeaways-edit-cancel"
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

          <Form.Group
            as={Row}
            controlId="takeawaysQbrLearning"
            className="mb-0 pl-1"
          >
            <Form.Group data-testid="takeaways-qbr" className="ml-3">
              <Form.Check
                type="checkbox"
                label="QBR Notable Learning"
                defaultChecked={isQbrLearning ? isQbrLearning : false}
                onChange={(e) => setIsQbrLearning(e.target.checked)}
                onSubmit={handleSave}
                id="takeawaysQbrLearning"
                {...{ "data-testid": "takeawaysQbrLearning" }}
              />
            </Form.Group>
          </Form.Group>
          <Form.Group as={Row} controlId="takeawaysMetricGain" className="pl-1">
            <Form.Group data-testid="takeaways-metric" className="ml-3">
              <Form.Check
                type="checkbox"
                label="Statistically Significant DAU Gain"
                defaultChecked={isMetricGain ? isMetricGain : false}
                onChange={(e) => setIsMetricGain(e.target.checked)}
                onSubmit={handleSave}
                id="takeawaysMetricGain"
                {...{ "data-testid": "takeawaysMetricGain" }}
              />
            </Form.Group>
          </Form.Group>

          <Form.Group as={Row}>
            <Form.Group
              as={Col}
              className="col-sm-2 col-md-2 ml-1"
              controlId="conclusionRecommendation"
            >
              <Form.Label
                className={classNames("font-weight-bold", {
                  "is-invalid": !!submitErrors["conclusion_recommendation"],
                })}
              >
                Recommendation:
              </Form.Label>
              <Form.Check
                type="radio"
                value=""
                label="None"
                title="None"
                {...conclusionRadioAttrs}
                id="conclusionRecommendation-none"
              />
              {conclusionRecommendations!.map((option, idx) => (
                <Form.Check
                  key={idx}
                  type="radio"
                  value={option!.value!}
                  label={option!.label!}
                  title={option!.label!}
                  {...conclusionRadioAttrs}
                  id={`conclusionRecommendation-${option!.value!}`}
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

          <Form.Group as={Row} controlId="takeaways-gain" className="ml-1">
            <Form.Label className="font-weight-bold">Gain Amount:</Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              placeholder="Examples: 0.5% gain in retention, or 0.5% gain in days of use"
              {...formControlAttrs("takeawaysGainAmount")}
            />
          </Form.Group>
        </Form>
      </FormProvider>
    </section>
  );
};

export default TakeawaysEditor;
