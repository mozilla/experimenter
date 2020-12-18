/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, act, fireEvent } from "@testing-library/react";
import { mockExperimentQuery } from "../../lib/mocks";
import { Subject } from "./mocks";

describe("FormOverview", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () =>
      expect(screen.getByTestId("FormOverview")).toBeInTheDocument(),
    );
  });

  it("calls onCancel when cancel clicked", async () => {
    const onCancel = jest.fn();
    render(<Subject {...{ onCancel }} />);

    const cancelButton = screen.getByText("Cancel");
    await act(async () => void fireEvent.click(cancelButton));
    expect(onCancel).toHaveBeenCalled();
  });

  it("calls onNext when next clicked", async () => {
    const onNext = jest.fn();
    render(<Subject {...{ onNext }} />);

    const nextButton = screen.getByText("Next");
    await act(async () => void fireEvent.click(nextButton));
    expect(onNext).toHaveBeenCalled();
  });

  const fillOutNewForm = async (expected: Record<string, string>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Application", expected.application],
    ]) {
      const fieldName = screen.getByLabelText(labelText);

      await act(async () => {
        fireEvent.click(fieldName);
        fireEvent.blur(fieldName);
      });
      if (labelText !== "Hypothesis") {
        expect(fieldName).toHaveClass("is-invalid");
        expect(fieldName).not.toHaveClass("is-valid");
      }

      await act(async () => {
        fireEvent.change(fieldName, { target: { value: fieldValue } });
        fireEvent.blur(fieldName);
      });
      expect(fieldName).not.toHaveClass("is-invalid");
      expect(fieldName).toHaveClass("is-valid");
    }
  };

  const checkExistingForm = async (expected: Record<string, string>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Public description", expected.publicDescription],
    ]) {
      const fieldName = screen.getByLabelText(labelText) as HTMLInputElement;
      expect(fieldName.value).toEqual(fieldValue);
    }
  };

  it("validates fields before allowing submit", async () => {
    const expected = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "DESKTOP",
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);

    const submitButton = screen.getByText("Create experiment");
    await act(async () => fillOutNewForm(expected));
    await act(async () => void fireEvent.click(submitButton));

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("with existing experiment data, asserts field values before allowing submit and next", async () => {
    const { experiment } = mockExperimentQuery("boo");

    const expected = {
      name: experiment.name,
      hypothesis: experiment.hypothesis as string,
      publicDescription: experiment.publicDescription as string,
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment, onNext: jest.fn() }} />);
    const submitButton = screen.getByText("Save");
    const nextButton = screen.getByText("Next");
    const nameField = screen.getByLabelText("Public name");

    expect(nextButton).toBeEnabled();

    await act(async () => checkExistingForm(expected));

    await act(async () => {
      fireEvent.change(nameField, { target: { value: "" } });
      fireEvent.blur(nameField);
    });

    // Update the name in the form and expected data
    const newName = "Name THIS";
    expected.name = newName;
    await act(async () => {
      fireEvent.change(nameField, {
        target: { value: newName },
      });
      fireEvent.blur(nameField);
    });
    expect(submitButton).toBeEnabled();

    await act(async () => void fireEvent.click(submitButton));
    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("with missing public description, still allows submit", async () => {
    const { experiment } = mockExperimentQuery("boo");

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment }} />);
    const descriptionField = screen.getByLabelText("Public description");
    const submitButton = screen.getByText("Save");

    await act(async () => {
      fireEvent.change(descriptionField, { target: { value: "" } });
      fireEvent.blur(descriptionField);
    });

    expect(submitButton).toBeEnabled();

    await act(async () => void fireEvent.click(submitButton));
    expect(onSubmit).toHaveBeenCalled();
  });

  it("disables create submission when loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);

    // Fill out valid form to ensure only isLoading prevents submission
    await act(
      async () =>
        void fillOutNewForm({
          name: "Foo bar baz",
          hypothesis: "Some thing",
          application: "DESKTOP",
        }),
    );

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent("Submitting");

    await act(async () => {
      fireEvent.click(submitButton);
      fireEvent.submit(screen.getByTestId("FormOverview"));
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("displays saving button when loading", async () => {
    const { experiment } = mockExperimentQuery("boo");
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment, isLoading: true }} />);

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toHaveTextContent("Saving");
  });

  it("displays an alert for overall submit error", async () => {
    const submitErrors = {
      "*": ["Big bad happened"],
    };
    render(<Subject {...{ submitErrors }} />);
    await act(async () =>
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        submitErrors["*"][0],
      ),
    );
  });

  it("displays feedback for per-field error", async () => {
    const submitErrors = {
      name: ["That name is terrible, man"],
    };
    render(<Subject {...{ submitErrors }} />);
    const errorFeedback = screen.getByText(submitErrors["name"][0]);
    await act(async () => {
      expect(errorFeedback).toHaveClass("invalid-feedback");
      expect(errorFeedback).toHaveAttribute("data-for", "name");
    });
  });

  it("displays warning icon when public description is not filled out and server requires it", async () => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });

    const { experiment } = mockExperimentQuery("boo");
    const isMissingField = jest.fn(() => true);
    render(<Subject {...{ isMissingField, experiment }} />);

    expect(isMissingField).toHaveBeenCalled();
    expect(screen.queryByTestId("missing-description")).toBeInTheDocument();
  });
});
