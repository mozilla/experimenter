/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import { FieldError } from "react-hook-form";
import { useCommonNestedForm } from "../../../hooks";
import { ReactComponent as DeleteIcon } from "../../../images/x.svg";
import { NUMBER_FIELD, REQUIRED_FIELD } from "../../../lib/constants";
import FormScreenshot, { FormScreenshotProps } from "./FormScreenshot";
import { AnnotatedBranch } from "./reducer";

export const branchFieldNames = [
  "name",
  "description",
  "ratio",
  "featureValue",
  "featureEnabled",
] as const;

type BranchFieldName = typeof branchFieldNames[number];

export const FormBranch = ({
  fieldNamePrefix,
  touched,
  errors,
  reviewErrors,
  reviewWarnings,
  branch,
  equalRatio,
  isReference,
  onAddScreenshot,
  onRemoveScreenshot,
  onRemove,
  defaultValues,
  setSubmitErrors,
}: {
  fieldNamePrefix: string;
  touched: Record<string, boolean>;
  errors: Record<string, FieldError>;
  reviewErrors: SerializerSet;
  reviewWarnings: SerializerSet;
  branch: AnnotatedBranch;
  equalRatio?: boolean;
  isReference?: boolean;
  onAddScreenshot: () => void;
  onRemoveScreenshot: (screenshotIdx: number) => void;
  onRemove?: () => void;
  defaultValues: Record<string, any>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
}) => {
  const id = fieldNamePrefix;
  const submitErrors = { ...branch.errors };

  const { FormErrors, formControlAttrs, watch } =
    useCommonNestedForm<BranchFieldName>(
      defaultValues,
      setSubmitErrors,
      fieldNamePrefix,
      submitErrors,
      errors,
      touched,
      reviewErrors,
      reviewWarnings,
    );

  const featureEnabled = watch(`${fieldNamePrefix}.featureEnabled`);

  const handleRemoveClick = () => onRemove && onRemove();

  const AddScreenshotButton = () => (
    <Button
      data-testid="add-screenshot"
      variant="outline-primary"
      size="sm"
      onClick={onAddScreenshot}
    >
      + Add screenshot
    </Button>
  );

  const addScreenshotButtonAtEnd =
    branch.screenshots && branch.screenshots.length > 0;

  return (
    <div
      className="mb-3 border border-secondary rounded"
      data-testid="FormBranch"
    >
      <Form.Group className="p-1 mx-3 mt-2 mb-0">
        <Form.Row>
          <Form.Group as={Col} controlId={`${id}-name`} sm={4} md={3}>
            <Form.Label>
              Branch{" "}
              {isReference && (
                <Badge pill variant="primary" data-testid="control-pill">
                  control
                </Badge>
              )}
            </Form.Label>
            <Form.Control
              {...formControlAttrs("name", REQUIRED_FIELD)}
              type="text"
            />
            <FormErrors name="name" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-description`}>
            <Form.Label>Description</Form.Label>
            <Form.Control {...formControlAttrs("description")} type="text" />
            <FormErrors name="description" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-ratio`} sm={2} md={2}>
            <Form.Label>Ratio</Form.Label>
            {equalRatio ? (
              <p data-testid="equal-ratio" className="p-0 m-0">
                Equal
                <Form.Control
                  {...formControlAttrs(
                    "ratio",
                    {
                      valueAsNumber: true,
                    },
                    false,
                  )}
                  type="hidden"
                  value="1"
                />
              </p>
            ) : (
              <>
                <Form.Control
                  {...formControlAttrs("ratio", {
                    valueAsNumber: true,
                    ...NUMBER_FIELD,
                  })}
                  type="number"
                  min="1"
                />
                <FormErrors name="ratio" />
              </>
            )}
          </Form.Group>
          <Form.Group as={Col} sm={1} className="align-top text-right">
            {!isReference && onRemove && (
              <Button
                data-testid="remove-branch"
                variant="light"
                className="bg-transparent border-0 p-0 m-0"
                title="Remove branch"
                onClick={handleRemoveClick}
              >
                <DeleteIcon width="18" height="18" />
              </Button>
            )}
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <Form.Group
        className="p-1 mx-3 mt-2 mb-0"
        data-testid="feature-config-edit"
      >
        <Form.Row>
          <Col sm={1} md={1}>
            Feature is
          </Col>
          <Form.Group as={Col} controlId={`${id}.featureEnabled`}>
            <Form.Check
              {...formControlAttrs("featureEnabled", {}, false)}
              type="switch"
              label={featureEnabled ? "On" : "Off"}
            />
            <FormErrors name="featureEnabled" />
          </Form.Group>
        </Form.Row>
      </Form.Group>
      <Form.Group
        className="p-1 mx-3 mt-2 mb-0"
        data-testid="feature-config-edit"
      >
        {featureEnabled ? (
          <Form.Row data-testid="feature-value-edit">
            <Form.Group as={Col} controlId={`${id}-featureValue`}>
              <Form.Label>Value</Form.Label>
              <Form.Control
                {...formControlAttrs("featureValue")}
                as="textarea"
                rows={4}
              />
              <FormErrors name="featureValue" />
            </Form.Group>
          </Form.Row>
        ) : (
          <Form.Control
            {...formControlAttrs("featureValue", {}, false)}
            type="hidden"
            value=""
          />
        )}
      </Form.Group>
      <Form.Group
        className="px-3 pt-2 border-top"
        data-testid="screenshots-edit"
      >
        <Form.Row className="my-3">
          <Col>Screenshots</Col>
          {!addScreenshotButtonAtEnd && (
            <Form.Group
              data-testid="add-screenshots-in-header"
              as={Col}
              className="align-top text-right"
            >
              <AddScreenshotButton />
            </Form.Group>
          )}
        </Form.Row>
        {branch.screenshots?.map((screenshot, idx) => (
          <div key={idx}>
            <FormScreenshot
              {...{
                fieldNamePrefix: `${fieldNamePrefix}.screenshots[${idx}]`,
                onRemove: () => onRemoveScreenshot!(idx),
                defaultValues: defaultValues.screenshots?.[idx] || {},
                setSubmitErrors,
                //@ts-ignore react-hook-form types seem broken for nested fields
                submitErrors: (submitErrors?.screenshots?.[idx] ||
                  {}) as FormScreenshotProps["submitErrors"],
                //@ts-ignore react-hook-form types seem broken for nested fields
                errors: (errors?.screenshots?.[idx] ||
                  {}) as FormScreenshotProps["errors"],
                //@ts-ignore react-hook-form types seem broken for nested fields
                touched: (touched?.screenshots?.[idx] ||
                  {}) as FormScreenshotProps["touched"],
                //@ts-ignore react-hook-form types seem broken for nested fields
                reviewErrors: (reviewErrors?.screenshots?.[idx] ||
                  {}) as FormScreenshotProps["reviewErrors"],
                //@ts-ignore react-hook-form types seem broken for nested fields
                reviewWarnings: (reviewWarnings?.screenshots?.[idx] ||
                  {}) as FormScreenshotProps["reviewWarnings"],
              }}
            />
            {branch?.screenshots && idx !== branch.screenshots.length - 1 && (
              <hr />
            )}
          </div>
        ))}
        {addScreenshotButtonAtEnd && (
          <Form.Row
            data-testid="add-screenshots-at-end"
            className="align-top text-right justify-content-end"
          >
            <AddScreenshotButton />
          </Form.Row>
        )}
      </Form.Group>
    </div>
  );
};

export default FormBranch;
