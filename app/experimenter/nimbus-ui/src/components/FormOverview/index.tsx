/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import ReactTooltip from "react-tooltip";
import { useCommonForm, useExitWarning } from "../../hooks";
import { useConfig } from "../../hooks/useConfig";
import { ReactComponent as Info } from "../../images/info.svg";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";
import { EXTERNAL_URLS } from "../../lib/constants";
import { getExperiment } from "../../types/getExperiment";
import { NimbusDocumentationLinkTitle } from "../../types/globalTypes";
import InlineErrorIcon from "../InlineErrorIcon";
import LinkExternal from "../LinkExternal";

type FormOverviewProps = {
  isLoading: boolean;
  isServerValid: boolean;
  isMissingField?: (fieldName: string) => boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  experiment?: getExperiment["experimentBySlug"];
  onSubmit: (data: Record<string, any>, reset: Function) => void;
  onCancel?: (ev: React.FormEvent) => void;
  onNext?: (ev: React.FormEvent) => void;
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
  onNext,
}: FormOverviewProps) => {
  const { application, hypothesisDefault, documentationLink } = useConfig();

  const hasExistingDocLinks =
    experiment?.documentationLinks && experiment?.documentationLinks.length > 0;
  const defaultValues = {
    name: experiment?.name || "",
    hypothesis: experiment?.hypothesis || (hypothesisDefault as string).trim(),
    application: "",
    publicDescription: experiment?.publicDescription as string,
    riskMitigationLink: experiment?.riskMitigationLink as string,
    documentationLinks: (hasExistingDocLinks
      ? experiment?.documentationLinks!
      : [
          {
            title: "",
            link: "",
          },
        ]) as { title: NimbusDocumentationLinkTitle | ""; link: string }[],
  };

  const {
    FormErrors,
    formControlAttrs,
    isValid,
    isDirtyUnsaved,
    handleSubmit,
    reset,
    isSubmitted,
  } = useCommonForm<OverviewFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  const handleSubmitAfterValidation = useCallback(
    (data: Record<string, any>) => {
      if (isLoading) return;
      onSubmit(data, reset);
    },
    [isLoading, onSubmit, reset],
  );

  const handleCancel = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onCancel!(ev);
    },
    [onCancel],
  );

  const handleNext = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onNext!(ev);
    },
    [onNext],
  );

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(handleSubmitAfterValidation)}
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
          {...formControlAttrs("name")}
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
          {...formControlAttrs("hypothesis")}
          as="textarea"
          rows={5}
        />
        <Form.Text className="text-muted">
          You can add any supporting documents here.
        </Form.Text>
        <FormErrors name="hypothesis" />
      </Form.Group>
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
          <Form.Control {...formControlAttrs("application")} as="select">
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
              {...formControlAttrs("publicDescription", {})}
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
              {...formControlAttrs("riskMitigationLink", {})}
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
              {defaultValues.documentationLinks.map((docLink, docIdx) => (
                <Form.Group
                  className="mb-0"
                  data-testid="DocumentationLink"
                  key={`doc-link-${docIdx}`}
                >
                  <Form.Row>
                    <Form.Group as={Col} sm={4} md={3}>
                      <Form.Control as="select" defaultValue={docLink.title}>
                        <option value="" disabled>
                          Select document type...
                        </option>
                        {documentationLink &&
                          documentationLink.map((linkType, optIdx) => (
                            <option
                              key={`doc-link-${docIdx}-opt-${optIdx}`}
                              value={linkType!.value as string}
                            >
                              {linkType!.label}
                            </option>
                          ))}
                      </Form.Control>
                    </Form.Group>
                    <Form.Group as={Col}>
                      <Form.Control
                        placeholder="Link"
                        type="url"
                        defaultValue={docLink.link}
                      />
                    </Form.Group>
                    <Form.Group as={Col} className="flex-grow-0">
                      <Button
                        data-testid="remove-documentation-link"
                        variant="light"
                        className="bg-transparent border-0 p-0 m-0 mt-px"
                        title="Remove link"
                        onClick={() => {}}
                      >
                        <DeleteIcon width="18" height="18" />
                      </Button>
                    </Form.Group>
                  </Form.Row>
                </Form.Group>
              ))}
            </div>

            <div className="pt-2 mb-5 text-right">
              <Button
                data-testid="add-additional-link"
                variant="outline-primary"
                size="sm"
                onClick={() => {}}
              >
                + Add Link
              </Button>
            </div>
          </Form.Group>
        </>
      )}

      <div className="d-flex flex-row-reverse bd-highlight">
        {!!experiment && onNext && (
          <div className="p-2">
            <button
              onClick={handleNext}
              className="btn btn-secondary"
              disabled={isLoading}
              data-sb-kind="pages/EditBranches"
            >
              Next
            </button>
          </div>
        )}
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSubmit(handleSubmitAfterValidation)}
            className="btn btn-primary"
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
            <button onClick={handleCancel} className="btn btn-light">
              Cancel
            </button>
          </div>
        )}
      </div>
    </Form>
  );
};

export default FormOverview;
