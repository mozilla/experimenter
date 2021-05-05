/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useMemo } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import { FormProvider } from "react-hook-form";
import ReactTooltip from "react-tooltip";
import {
  SubmitErrorRecord,
  SubmitErrors,
  useCommonForm,
  useExitWarning,
} from "../../hooks";
import { useConfig } from "../../hooks/useConfig";
import { ReactComponent as Info } from "../../images/info.svg";
import { EXTERNAL_URLS, REQUIRED_FIELD, URL_FIELD } from "../../lib/constants";
import { optionalBoolString } from "../../lib/utils";
import { getExperiment } from "../../types/getExperiment";
import InlineErrorIcon from "../InlineErrorIcon";
import InputRadios from "../InputRadios";
import LinkExternal from "../LinkExternal";
import {
  stripInvalidDocumentationLinks,
  useDocumentationLinks,
} from "./documentationLink";
import FormDocumentationLink, {
  FormDocumentationLinkProps,
} from "./FormDocumentationLink";

type FormOverviewProps = {
  isLoading: boolean;
  isServerValid: boolean;
  isMissingField?: (fieldName: string) => boolean;
  submitErrors: SubmitErrors;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  experiment?: getExperiment["experimentBySlug"];
  onSubmit: (data: Record<string, any>, next: boolean) => void;
  onCancel?: (ev: React.FormEvent) => void;
};

export const DOCUMENTATION_LINKS_TOOLTIP =
  "Any additional links you would like to add, for example, Jira DS Ticket, Jira QA ticket, or experiment brief.";

export const overviewFieldNames = [
  "name",
  "hypothesis",
  "application",
  "publicDescription",
  "riskMitigationLink",
  "documentationLinks",
  "riskBrand",
  "riskRevenue",
  "riskPartnerRelated",
] as const;

type OverviewFieldName = typeof overviewFieldNames[number];

const FormOverview = ({
  isLoading,
  isServerValid,
  isMissingField,
  submitErrors,
  setSubmitErrors,
  experiment,
  onSubmit,
  onCancel,
}: FormOverviewProps) => {
  const { application, hypothesisDefault } = useConfig();

  const defaultValues = {
    name: experiment?.name || "",
    hypothesis: experiment?.hypothesis || (hypothesisDefault as string).trim(),
    application: "",
    publicDescription: experiment?.publicDescription as string,
    riskMitigationLink: experiment?.riskMitigationLink as string,
    riskBrand: optionalBoolString(experiment?.riskBrand),
    riskRevenue: optionalBoolString(experiment?.riskRevenue),
    riskPartnerRelated: optionalBoolString(experiment?.riskPartnerRelated),
  };

  const {
    FormErrors,
    formControlAttrs,
    isValid,
    isDirtyUnsaved,
    handleSubmit,
    isSubmitted,
    errors,
    touched,
    formMethods,
    control,
    setValue,
  } = useCommonForm<OverviewFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  const {
    documentationLinks,
    addDocumentationLink,
    removeDocumentationLink,
  } = useDocumentationLinks(experiment, control, setValue);

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  type DefaultValues = typeof defaultValues;
  const [handleSave, handleSaveNext] = useMemo(
    () =>
      [false, true].map((next) =>
        handleSubmit(
          (dataIn: DefaultValues) =>
            !isLoading &&
            onSubmit(stripInvalidDocumentationLinks(dataIn), next),
        ),
      ),
    [isLoading, onSubmit, handleSubmit],
  );

  const handleCancel = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onCancel!(ev);
    },
    [onCancel],
  );

  return (
    <FormProvider {...formMethods}>
      <Form
        noValidate
        onSubmit={handleSave}
        validated={isSubmitted && isValid}
        data-testid="FormOverview"
      >
        {submitErrors["*"] && (
          <Alert data-testid="submit-error" variant="warning">
            {submitErrors["*"]}
          </Alert>
        )}

        <Form.Group controlId="name">
          <Form.Label>Public name</Form.Label>
          <Form.Control
            {...formControlAttrs("name", REQUIRED_FIELD)}
            type="text"
            autoFocus={!experiment}
          />
          <Form.Text className="text-muted">
            This name will be public to users in about:studies.
          </Form.Text>
          <FormErrors name="name" />
        </Form.Group>

        <Form.Group controlId="hypothesis">
          <Form.Label>Hypothesis</Form.Label>
          <Form.Control
            {...formControlAttrs("hypothesis", REQUIRED_FIELD)}
            as="textarea"
            rows={5}
          />
          <Form.Text className="text-muted">
            You can add any supporting documents here.
          </Form.Text>
          <FormErrors name="hypothesis" />
        </Form.Group>

        {experiment && (
          <InputRadios
            name="riskBrand"
            options={[
              { label: "Yes", value: "true" },
              { label: "No", value: "false" },
            ]}
            {...{ FormErrors, formControlAttrs }}
          >
            If the public, users or press, were to discover this experiment and
            description, do you think it would negatively impact their
            perception of the brand?{" "}
            <LinkExternal href={EXTERNAL_URLS.SIGNOFF_BRAND}>
              Learn more
            </LinkExternal>
            {isMissingField!("risk_brand") && (
              <span className="align-text-bottom ml-1">
                <InlineErrorIcon
                  name="risk_brand"
                  message="Please answer this question"
                />
              </span>
            )}
          </InputRadios>
        )}

        <Form.Group controlId="application">
          <Form.Label>Application</Form.Label>
          {experiment ? (
            <Form.Control
              as="input"
              value={
                application!.find((a) => a?.value === experiment.application)
                  ?.label as string
              }
              readOnly
            />
          ) : (
            <Form.Control
              {...formControlAttrs("application", REQUIRED_FIELD)}
              as="select"
            >
              <option value="">Select...</option>
              {application!.map((app, idx) => (
                <option key={`application-${idx}`} value={app!.value as string}>
                  {app!.label}
                </option>
              ))}
            </Form.Control>
          )}
          <Form.Text className="text-muted">
            <p className="mb-0">
              Experiments can only target one Application at a time.
            </p>
            <p className="mb-0">
              Application can not be changed after an experiment is created.
            </p>
          </Form.Text>
          <FormErrors name="application" />
        </Form.Group>

        {experiment && (
          <>
            <Form.Group controlId="publicDescription">
              <Form.Label className="d-flex align-items-center">
                Public description
                {isMissingField!("public_description") && (
                  <InlineErrorIcon
                    name="description"
                    message="Public description cannot be blank"
                  />
                )}
              </Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                {...formControlAttrs("publicDescription")}
              />
              <Form.Text className="text-muted">
                This description will be public to users on about:studies
              </Form.Text>
              <FormErrors name="publicDescription" />
            </Form.Group>

            <Form.Group controlId="riskMitigationLink">
              <Form.Label className="d-flex align-items-center">
                Risk Mitigation Checklist Link
                {isMissingField!("risk_mitigation_link") && (
                  <InlineErrorIcon
                    name="risk_mitigation_link"
                    message="A Risk Mitigation Checklist is required"
                  />
                )}
              </Form.Label>
              <Form.Control
                {...formControlAttrs("riskMitigationLink", URL_FIELD)}
                type="url"
              />
              <Form.Text className="text-muted">
                Go to the{" "}
                <LinkExternal href={EXTERNAL_URLS.RISK_MITIGATION_TEMPLATE_DOC}>
                  risk mitigation checklist
                </LinkExternal>{" "}
                to make a copy and add the link above
              </Form.Text>
              <FormErrors name="riskMitigationLink" />
            </Form.Group>

            <InputRadios
              name="riskRevenue"
              options={[
                { label: "Yes", value: "true" },
                { label: "No", value: "false" },
              ]}
              {...{ FormErrors, formControlAttrs }}
            >
              Does this experiment impact or rely on a partner or outside
              company (e.g. Google, Amazon)?{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_PARTNER}>
                Learn more
              </LinkExternal>
              {isMissingField!("risk_partner_related") && (
                <span className="align-text-bottom ml-1">
                  <InlineErrorIcon
                    name="risk_partner_related"
                    message="Please answer this question"
                  />
                </span>
              )}
            </InputRadios>

            <InputRadios
              name="riskPartnerRelated"
              options={[
                { label: "Yes", value: "true" },
                { label: "No", value: "false" },
              ]}
              {...{ FormErrors, formControlAttrs }}
            >
              Does this experiment have a risk to negatively impact revenue
              (e.g. search, Pocket revenue)?{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_REVENUE}>
                Learn more
              </LinkExternal>
              {isMissingField!("risk_revenue") && (
                <span className="align-text-bottom ml-1">
                  <InlineErrorIcon
                    name="risk_revenue"
                    message="Please answer this question"
                  />
                </span>
              )}
            </InputRadios>

            <Form.Group controlId="documentationLinks">
              <Form.Label>
                Additional Links
                <Info
                  data-tip={DOCUMENTATION_LINKS_TOOLTIP}
                  data-testid="tooltip-documentation-links"
                  width="20"
                  height="20"
                  className="ml-1"
                />
                <ReactTooltip />
              </Form.Label>
              <div>
                {documentationLinks.map((documentationLink, index) => (
                  <FormDocumentationLink
                    key={documentationLink.id}
                    {...{
                      documentationLink,
                      setSubmitErrors,
                      fieldNamePrefix: `documentationLinks[${index}]`,
                      submitErrors:
                        (submitErrors?.documentation_links &&
                          (submitErrors?.documentation_links as SubmitErrorRecord[])[
                            index
                          ]) ||
                        {},
                      //@ts-ignore react-hook-form types seem broken for nested fields
                      errors: (errors?.documentationLinks?.[index] ||
                        {}) as FormDocumentationLinkProps["errors"],
                      //@ts-ignore react-hook-form types seem broken for nested fields
                      touched: (touched?.documentationLinks?.[index] ||
                        {}) as FormDocumentationLinkProps["touched"],
                      onRemove: () => {
                        removeDocumentationLink(documentationLink);
                      },
                      canRemove: index !== 0,
                    }}
                  />
                ))}
              </div>

              <div className="pt-2 mb-5 text-right">
                <Button
                  data-testid="add-additional-link"
                  variant="outline-primary"
                  size="sm"
                  onClick={addDocumentationLink}
                >
                  + Add Link
                </Button>
              </div>
            </Form.Group>
          </>
        )}

        <div className="d-flex flex-row-reverse bd-highlight">
          {!!experiment && (
            <div className="p-2">
              <button
                data-testid="next-button"
                onClick={handleSaveNext}
                className="btn btn-secondary"
                id="save-and-continue-button"
                disabled={isLoading}
                data-sb-kind="pages/EditBranches"
              >
                Save and Continue
              </button>
            </div>
          )}
          <div className="p-2">
            <button
              data-testid="submit-button"
              type="submit"
              onClick={handleSave}
              className="btn btn-primary"
              id="submit-button"
              disabled={isLoading}
              data-sb-kind="pages/EditOverview"
            >
              {isLoading ? (
                <span>{experiment ? "Saving" : "Submitting"}</span>
              ) : (
                <span>{experiment ? "Save" : "Next"}</span>
              )}
            </button>
          </div>
          {onCancel && (
            <div className="p-2">
              <button
                onClick={handleCancel}
                className="btn btn-light"
                id="cancel-button"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </Form>
    </FormProvider>
  );
};

export default FormOverview;
