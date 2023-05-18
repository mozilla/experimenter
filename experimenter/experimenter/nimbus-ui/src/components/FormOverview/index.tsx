/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import { FormProvider } from "react-hook-form";
import Select from "react-select";
import ReactTooltip from "react-tooltip";
import {
  stripInvalidDocumentationLinks,
  useDocumentationLinks,
} from "src/components/FormOverview/documentationLink";
import FormDocumentationLink, {
  FormDocumentationLinkProps,
} from "src/components/FormOverview/FormDocumentationLink";
import InputRadios from "src/components/InputRadios";
import LinkExternal from "src/components/LinkExternal";
import { useCommonForm, useExitWarning, useReviewCheck } from "src/hooks";
import { useConfig } from "src/hooks/useConfig";
import { ReactComponent as Info } from "src/images/info.svg";
import {
  EXTERNAL_URLS,
  PUBLIC_DESCRIPTION_PLACEHOLDER,
  REQUIRED_FIELD,
  RISK_QUESTIONS,
} from "src/lib/constants";
import { optionalBoolString } from "src/lib/utils";
import { getConfig_nimbusConfig_projects } from "src/types/getConfig";
import { getExperiment } from "src/types/getExperiment";

type FormOverviewProps = {
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: SerializerMessages;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  experiment?: getExperiment["experimentBySlug"];
  onSubmit: (data: Record<string, any>, next: boolean) => void;
  onCancel?: (ev: React.FormEvent) => void;
};
type SelectIdItems = (getConfig_nimbusConfig_projects | null)[];

export const DOCUMENTATION_LINKS_TOOLTIP =
  "Any additional links you would like to add, for example, Jira DS Ticket, Jira QA ticket, or experiment brief.";
export const overviewFieldNames = [
  "name",
  "hypothesis",
  "application",
  "publicDescription",
  "documentationLinks",
  "riskBrand",
  "riskRevenue",
  "riskPartnerRelated",
  "projects",
] as const;

const selectOptions = (items: SelectIdItems) =>
  items?.map((item) => ({
    label: item?.name!,
    value: item?.id!,
  }));

type OverviewFieldName = typeof overviewFieldNames[number];

const FormOverview = ({
  isLoading,
  isServerValid,
  submitErrors,
  setSubmitErrors,
  experiment,
  onSubmit,
  onCancel,
}: FormOverviewProps) => {
  const { applications, hypothesisDefault } = useConfig();
  const config = useConfig();
  const { fieldMessages, fieldWarnings } = useReviewCheck(experiment);
  const [projects, setProjects] = useState<string[]>(
    experiment!?.projects!?.map((v) => "" + v!.id!),
  );
  const defaultValues = {
    name: experiment?.name || "",
    hypothesis: experiment?.hypothesis || (hypothesisDefault as string).trim(),
    application: "",
    publicDescription: experiment?.publicDescription as string,
    riskBrand: optionalBoolString(experiment?.riskBrand),
    riskRevenue: optionalBoolString(experiment?.riskRevenue),
    riskPartnerRelated: optionalBoolString(experiment?.riskPartnerRelated),
    projects: selectOptions(experiment?.projects as SelectIdItems),
  };
  const {
    FormErrors,
    formControlAttrs,
    formSelectAttrs,
    isValid,
    isDirtyUnsaved,
    handleSubmit,
    isSubmitted,
    errors,
    touched,
    formMethods,
    control,
    setValue,
    watch,
  } = useCommonForm<OverviewFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
    fieldMessages,
    fieldWarnings,
  );

  const isArchived =
    experiment?.isArchived != null ? experiment.isArchived : false;

  const { documentationLinks, addDocumentationLink, removeDocumentationLink } =
    useDocumentationLinks(experiment, control, setValue);

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
            onSubmit(
              { ...stripInvalidDocumentationLinks(dataIn), projects },
              next,
            ),
        ),
      ),
    [handleSubmit, isLoading, onSubmit, projects],
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
            {...formControlAttrs("name", {
              ...REQUIRED_FIELD,
              maxLength: {
                value: 80,
                message: "Cannot be greater than 80 characters",
              },
            })}
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
            {RISK_QUESTIONS.BRAND}{" "}
            <LinkExternal href={EXTERNAL_URLS.RISK_BRAND}>
              Learn more
            </LinkExternal>
          </InputRadios>
        )}

        <Form.Group controlId="application">
          <Form.Label>Application</Form.Label>
          {experiment ? (
            <Form.Control
              as="input"
              value={
                applications!.find((a) => a?.value === experiment.application)
                  ?.label as string
              }
              readOnly
            />
          ) : (
            <Form.Control
              {...formControlAttrs("application", REQUIRED_FIELD)}
              as="select"
              custom
            >
              <option value="">Select...</option>
              {applications!.map((app, idx) => (
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
          <Form.Group controlId="projects" data-testid="projects">
            <Form.Label>Team Projects</Form.Label>
            <Select
              placeholder="Select Team..."
              isMulti
              {...formSelectAttrs("projects", setProjects)}
              options={selectOptions(config.projects as SelectIdItems)}
            />
            <FormErrors name="projects" />
          </Form.Group>
        )}

        {experiment && (
          <>
            <Form.Group controlId="publicDescription">
              <Form.Label className="d-flex align-items-center">
                Public description
              </Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder={PUBLIC_DESCRIPTION_PLACEHOLDER}
                {...formControlAttrs("publicDescription")}
              />
              <Form.Text className="text-muted">
                This description will be public to users on about:studies
              </Form.Text>
              <FormErrors name="publicDescription" />
            </Form.Group>

            <InputRadios
              name="riskRevenue"
              options={[
                { label: "Yes", value: "true" },
                { label: "No", value: "false" },
              ]}
              {...{ FormErrors, formControlAttrs }}
            >
              {RISK_QUESTIONS.REVENUE}{" "}
              <LinkExternal href={EXTERNAL_URLS.RISK_REVENUE}>
                Learn more
              </LinkExternal>
            </InputRadios>

            <InputRadios
              name="riskPartnerRelated"
              options={[
                { label: "Yes", value: "true" },
                { label: "No", value: "false" },
              ]}
              {...{ FormErrors, formControlAttrs }}
            >
              {RISK_QUESTIONS.PARTNER}{" "}
              <LinkExternal href={EXTERNAL_URLS.RISK_PARTNER}>
                Learn more
              </LinkExternal>
            </InputRadios>

            <Form.Group controlId="documentationLinks" id="documentation-links">
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
                        (submitErrors as SerializerMessages<SerializerSet[]>)
                          .documentation_links?.[index] || {},
                      reviewMessages:
                        (fieldMessages as SerializerMessages<SerializerSet[]>)
                          .documentation_links?.[index] || {},
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
                disabled={isLoading || isArchived}
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
              disabled={isLoading || isArchived}
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
