/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  render,
  screen,
  act,
  fireEvent,
  cleanup,
} from "@testing-library/react";
import FormExperimentOverviewPartial from ".";

describe("FormExperimentOverviewPartial", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () => {
      expect(
        screen.getByTestId("FormExperimentOverviewPartial"),
      ).toBeInTheDocument();
    });
  });

  it("calls onCancel when cancel clicked", async () => {
    const onCancel = jest.fn();
    render(<Subject {...{ onCancel }} />);
    await act(async () => {
      const cancelButton = screen.getByText("Cancel");
      await fireEvent.click(cancelButton);
      expect(onCancel).toHaveBeenCalled();
    });
  });

  const fillOutForm = async (expected: Record<string, string>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Application", expected.application],
    ]) {
      const fieldName = screen.getByLabelText(labelText);
      expect(fieldName).not.toHaveClass("is-invalid");
      expect(fieldName).not.toHaveClass("is-valid");
      await fireEvent.click(fieldName);
      await fireEvent.blur(fieldName);
      expect(fieldName).toHaveClass("is-invalid");
      expect(fieldName).not.toHaveClass("is-valid");
      await fireEvent.change(fieldName, { target: { value: fieldValue } });
      await fireEvent.blur(fieldName);
      expect(fieldName).not.toHaveClass("is-invalid");
      expect(fieldName).toHaveClass("is-valid");
    }
  };

  it("validates fields before allowing submit", async () => {
    const expected = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "firefox-desktop",
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);

    await act(async () => {
      const submitButton = screen.getByText("Create experiment");
      await fireEvent.click(submitButton);
      expect(onSubmit).not.toHaveBeenCalled();
    });

    await act(async () => {
      await fillOutForm(expected);
    });

    await act(async () => {
      const submitButton = screen.getByText("Create experiment");
      await fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("disables submission when loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);

    // Fill out valid form to ensure only isLoading prevents submission
    await act(async () => {
      await fillOutForm({
        name: "Foo bar baz",
        hypothesis: "Some thing",
        application: "firefox-desktop",
      });
    });

    await act(async () => {
      const submitButton = screen.getByTestId("submit-button");
      expect(submitButton).toBeDisabled();
      await fireEvent.click(submitButton);
      await fireEvent.submit(
        screen.getByTestId("FormExperimentOverviewPartial"),
      );
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("displays an alert for overall submit error", async () => {
    const submitErrors = {
      "*": "Big bad happened",
    };
    render(<Subject {...{ submitErrors }} />);
    await act(async () => {
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        submitErrors["*"],
      );
    });
  });

  it("displays feedback for per-field error", async () => {
    const submitErrors = {
      "name": "That name is terrble, man",
    };
    render(<Subject {...{ submitErrors }} />);
    await act(async () => {
      const errorFeedback = screen.getByText(submitErrors['name']);      
      expect(errorFeedback).toHaveClass('invalid-feedback');
      expect(errorFeedback).toHaveAttribute('data-for', 'name');
    });
  });
});

const APPLICATIONS = ["firefox-desktop", "fenix", "reference-browser"];

const Subject = ({
  isLoading = false,
  submitErrors = {},
  onSubmit = jest.fn(),
  onCancel = jest.fn(),
  applications = APPLICATIONS,
} = {}) => (
  <FormExperimentOverviewPartial
    {...{ isLoading, submitErrors, onSubmit, onCancel, applications }}
  />
);
