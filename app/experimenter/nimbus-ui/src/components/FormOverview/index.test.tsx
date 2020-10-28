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
import FormOverview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { getExperiment } from "../../types/getExperiment";

describe("FormOverview", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () => {
      expect(screen.getByTestId("FormOverview")).toBeInTheDocument();
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

  it("calls onNext when next clicked", async () => {
    const onNext = jest.fn();
    render(<Subject {...{ onNext }} />);
    await act(async () => {
      const nextButton = screen.getByText("Next");
      await fireEvent.click(nextButton);
      expect(onNext).toHaveBeenCalled();
    });
  });

  const fillOutNewForm = async (expected: Record<string, string>) => {
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

  const checkExistingForm = async (expected: Record<string, string>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Application", expected.application],
      ["Public Description", expected.publicDescription],
    ]) {
      const fieldName = screen.getByLabelText(labelText) as HTMLInputElement;
      expect(fieldName.value).toEqual(fieldValue);
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
      await fillOutNewForm(expected);
    });

    await act(async () => {
      const submitButton = screen.getByText("Create experiment");
      await fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("with missing public description, does not allow submit", async () => {
    const { data } = mockExperimentQuery("boo", { publicDescription: "" });

    const expected = {
      name: data!.name,
      hypothesis: data!.hypothesis as string,
      application: (data!.application as string)
        .toLowerCase()
        .replace(/_/g, "-"),
      publicDescription: "",
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment: data }} />);

    await act(async () => {
      await checkExistingForm(expected);
    });

    await act(async () => {
      const submitButton = screen.getByText("Save");
      await fireEvent.click(submitButton);
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  it("with existing experiment data, asserts field values before allowing submit", async () => {
    const { data } = mockExperimentQuery("boo");

    const expected = {
      name: data!.name,
      hypothesis: data!.hypothesis as string,
      application: (data!.application as string)
        .toLowerCase()
        .replace(/_/g, "-"),
      publicDescription: data!.publicDescription as string,
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment: data }} />);

    await act(async () => {
      const submitButton = screen.getByText("Save");
      await fireEvent.click(submitButton);
      expect(onSubmit).not.toHaveBeenCalled();
    });

    await act(async () => {
      await checkExistingForm(expected);
    });

    await act(async () => {
      const submitButton = screen.getByText("Save");
      await fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("disables create submission when loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);

    // Fill out valid form to ensure only isLoading prevents submission
    await act(async () => {
      await fillOutNewForm({
        name: "Foo bar baz",
        hypothesis: "Some thing",
        application: "firefox-desktop",
      });
    });

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent("Submitting");

    await act(async () => {
      await fireEvent.click(submitButton);
      await fireEvent.submit(screen.getByTestId("FormOverview"));
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("displays saving button when loading", async () => {
    const { data } = mockExperimentQuery("boo");
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment: data, isLoading: true }} />);

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toHaveTextContent("Saving");
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
      name: "That name is terrble, man",
    };
    render(<Subject {...{ submitErrors }} />);
    await act(async () => {
      const errorFeedback = screen.getByText(submitErrors["name"]);
      expect(errorFeedback).toHaveClass("invalid-feedback");
      expect(errorFeedback).toHaveAttribute("data-for", "name");
    });
  });
});

const APPLICATIONS = ["firefox-desktop", "fenix", "reference-browser"];

const Subject = ({
  isLoading = false,
  submitErrors = {},
  onSubmit = jest.fn(),
  onCancel = jest.fn(),
  onNext = jest.fn(),
  applications = APPLICATIONS,
  experiment,
}: {
  [key: string]: any;
  experiment?: getExperiment["experimentBySlug"];
} = {}) => (
  <FormOverview
    {...{
      isLoading,
      submitErrors,
      onSubmit,
      onCancel,
      onNext,
      applications,
      experiment,
    }}
  />
);
