/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import { ArrayField, FieldError } from "react-hook-form";
import { useCommonNestedForm, useConfig } from "../../hooks";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";
import { AnnotatedDocumentationLink } from "./documentationLink";

export const documentationLinkFieldNames = ["title", "link"] as const;

type DocumentationLinkFieldName = typeof documentationLinkFieldNames[number];

export type FormDocumentationLinkProps = {
  fieldNamePrefix: string;
  documentationLink: Partial<ArrayField<AnnotatedDocumentationLink, "id">>;
  errors: Record<string, FieldError>;
  onRemove: () => void;
  canRemove: boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  touched: Record<string, boolean>;
};

export const FormDocumentationLink = ({
  fieldNamePrefix,
  documentationLink,
  errors,
  onRemove,
  canRemove,
  submitErrors,
  setSubmitErrors,
  touched,
}: FormDocumentationLinkProps) => {
  const { documentationLink: documentationLinkOptions } = useConfig();

  const { FormErrors, formControlAttrs } = useCommonNestedForm<
    DocumentationLinkFieldName
  >(
    {
      title: documentationLink.title,
      link: documentationLink.link,
    },
    setSubmitErrors,
    fieldNamePrefix,
    submitErrors,
    errors,
    touched,
  );

  return (
    <Form.Group className="mb-0" data-testid="DocumentationLink">
      <Form.Row>
        <Form.Group as={Col} sm={4} md={3}>
          <Form.Control as="select" {...formControlAttrs("title")}>
            <option value="">Select document type...</option>
            {documentationLinkOptions &&
              documentationLinkOptions.map((linkType, optIdx) => (
                <option
                  key={`${documentationLink.id}-opt-${optIdx}`}
                  value={linkType!.value as string}
                >
                  {linkType!.label}
                </option>
              ))}
          </Form.Control>
          <FormErrors name="title" />
        </Form.Group>
        <Form.Group as={Col}>
          <Form.Control
            placeholder="Link"
            type="url"
            {...formControlAttrs("link")}
          />
          <FormErrors name="link" />
        </Form.Group>
        {canRemove && (
          <Form.Group as={Col} className="flex-grow-0">
            <Button
              data-testid={`${fieldNamePrefix}.remove`}
              variant="light"
              className="bg-transparent border-0 p-0 m-0 mt-px"
              title="Remove link"
              onClick={onRemove}
            >
              <DeleteIcon width="18" height="18" />
            </Button>
          </Form.Group>
        )}
      </Form.Row>
    </Form.Group>
  );
};

export default FormDocumentationLink;
