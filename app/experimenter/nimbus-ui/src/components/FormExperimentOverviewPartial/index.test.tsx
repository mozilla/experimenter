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
    });

    await act(async () => {
      const submitButton = screen.getByText("Create experiment");
      await fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });
});

const APPLICATIONS = ["firefox-desktop", "fenix", "reference-browser"];

const Subject = ({
  onSubmit = jest.fn(),
  onCancel = jest.fn(),
  applications = APPLICATIONS,
} = {}) => (
  <FormExperimentOverviewPartial {...{ onSubmit, onCancel, applications }} />
);
