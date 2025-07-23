/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React from "react";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Image from "react-bootstrap/Image";
import Row from "react-bootstrap/Row";
import { Controller, FieldError } from "react-hook-form";
import { useCommonNestedForm } from "src/hooks";
import { ReactComponent as DeleteIcon } from "src/images/x.svg";
import { IMAGE_UPLOAD_ACCEPT } from "src/lib/constants";

export const screenshotFieldNames = ["description", "image"] as const;

type ScreenshotFieldName = typeof screenshotFieldNames[number];

export type FormScreenshotProps = {
  defaultValues: Record<string, any>;
  errors: Record<string, FieldError>;
  fieldNamePrefix: string;
  onRemove: () => void;
  reviewErrors: SerializerSet;
  reviewWarnings: SerializerSet;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  submitErrors: { [x: string]: SerializerMessage };
  touched: Record<string, boolean>;
};

export const FormScreenshot = ({
  defaultValues,
  errors,
  fieldNamePrefix,
  onRemove,
  reviewErrors,
  reviewWarnings,
  setSubmitErrors,
  submitErrors,
  touched,
}: FormScreenshotProps) => {
  const { FormErrors, formControlAttrs } =
    useCommonNestedForm<ScreenshotFieldName>(
      defaultValues,
      setSubmitErrors,
      fieldNamePrefix,
      submitErrors,
      errors,
      touched,
      reviewErrors,
      reviewWarnings,
    );

  const imageProps = formControlAttrs("image");

  return (
    <Form.Group className="mt-2" data-testid="FormScreenshot">
      <Form.Group controlId={`${fieldNamePrefix}-description`}>
        <Form.Label className="w-100">
          <Row className="w-100">
            <Col>Description</Col>
            <Col className="text-right">
              <Button
                data-testid="remove-screenshot"
                variant="light"
                className="bg-transparent border-0 p-0 m-0"
                title="Remove screenshot"
                onClick={onRemove}
              >
                <DeleteIcon width="18" height="18" />
              </Button>
            </Col>
          </Row>
        </Form.Label>
        <Form.Control
          {...formControlAttrs("description")}
          as="textarea"
          rows={2}
        />
        <FormErrors name="description" />
      </Form.Group>
      <Form.Group controlId={`${fieldNamePrefix}-image`}>
        <Form.Label>Image</Form.Label>
        <Controller
          name={imageProps.name}
          defaultValue={imageProps.defaultValue}
          render={({ onChange, onBlur, value, name, ref }) => {
            const {
              "data-testid": dataTestId,
              className,
              isInvalid,
              isValid,
            } = imageProps;
            return (
              <>
                <Form.File custom>
                  <Form.File.Input
                    {...{
                      "data-testid": dataTestId,
                      className: classNames(className, "text-nowrap"),
                      isInvalid,
                      isValid,
                      name,
                      ref,
                      onBlur,
                      accept: IMAGE_UPLOAD_ACCEPT,
                      onChange: (ev: React.ChangeEvent<HTMLInputElement>) => {
                        imageProps.onChange?.();
                        return onChange(ev.target.files?.[0]);
                      },
                    }}
                  />
                  <Form.File.Label data-testid="upload-label">
                    {uploadToLabel(value)}
                  </Form.File.Label>
                  <FormErrors name="image" />
                </Form.File>
                <UploadPreviewImage upload={value} />
              </>
            );
          }}
        />
      </Form.Group>
    </Form.Group>
  );
};

function uploadToLabel(upload: Upload | null) {
  if (upload) {
    if (typeof upload === "string") {
      return upload;
    } else if (typeof upload === "object" && "name" in upload) {
      return upload.name;
    }
  }
  return ""; // null or :shrug:
}

const UploadPreviewImage = ({ upload }: { upload: Upload | null }) => {
  let previewUrl = null;
  if (upload) {
    if (typeof upload === "string") {
      previewUrl = upload;
    } else if (typeof upload === "object" && "name" in upload) {
      previewUrl = URL.createObjectURL(upload);
    }
  }
  if (!previewUrl) return null;
  return (
    <Image
      data-testid="upload-preview"
      fluid
      className="mt-4"
      alt={`${uploadToLabel(upload)} preview`}
      src={previewUrl}
    />
  );
};

export default FormScreenshot;
