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
import { NimbusExperimentConclusionRecommendationEnum } from "src/types/globalTypes";

export const takeawaysEditorFieldNames = [
  "conclusionRecommendations",
  "takeawaysSummary",
  "takeawaysQbrLearning",
  "takeawaysMetricGain",
  "takeawaysGainAmount",
] as const;

type TakeawaysEditorFieldName = typeof takeawaysEditorFieldNames[number];

export type TakeawaysEditorProps = UseTakeawaysResult &
  Pick<getConfig_nimbusConfig, "conclusionRecommendationsChoices"> & {
    setShowEditor: (state: boolean) => void;
  };

export const TakeawaysEditor = ({
  isLoading,
  conclusionRecommendationsChoices,
  conclusionRecommendations,
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
    conclusionRecommendations,
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
    data.conclusionRecommendations = updatedRecommendations;
    await onSubmit(data);
  });

  const [updatedRecommendations, setUpdatedRecommendations] = useState<
    NimbusExperimentConclusionRecommendationEnum[]
  >(conclusionRecommendations);

  const updateRecommendations = useCallback(
    (updatedRecs: NimbusExperimentConclusionRecommendationEnum[]) => {
      setUpdatedRecommendations(updatedRecs);
    },
    [],
  );

  const handleCheckboxChange = (
    value: NimbusExperimentConclusionRecommendationEnum,
    checked: boolean,
  ) => {
    let updatedRecs = [...updatedRecommendations];

    if (checked && !updatedRecs.includes(value)) {
      updatedRecs.push(value);
    } else if (!checked && updatedRecs.includes(value)) {
      updatedRecs = updatedRecs.filter((item) => item !== value);
    }

    updateRecommendations(updatedRecs);
  };

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
                onChange={(e: { target: { checked: boolean } }) =>
                  setIsQbrLearning(e.target.checked)
                }
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
                onChange={(e: { target: { checked: boolean } }) =>
                  setIsMetricGain(e.target.checked)
                }
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
              controlId="conclusionRecommendations"
            >
              <Form.Label
                className={classNames("font-weight-bold", {
                  "is-invalid": !!submitErrors["conclusion_recommendations"],
                })}
              >
                Conclusion Recommendations:
              </Form.Label>
              {conclusionRecommendationsChoices?.map((option, idx) => (
                <Form.Check
                  key={idx}
                  type="checkbox"
                  label={option?.label}
                  checked={updatedRecommendations.includes(
                    option?.value as NimbusExperimentConclusionRecommendationEnum,
                  )}
                  onChange={(e: any) =>
                    handleCheckboxChange(
                      option?.value as NimbusExperimentConclusionRecommendationEnum,
                      e.target.checked,
                    )
                  }
                  id={`conclusionRecommendations-${option?.value}`}
                  data-testid={`conclusionRecommendations-${option?.value}`}
                />
              ))}
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
