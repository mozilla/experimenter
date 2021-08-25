/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import CloneDialog from ".";
import { mockExperimentQuery } from "../../../lib/mocks";

describe("CloneDialog", () => {
  it("renders, cancels, and saves as expected", async () => {
    const onSave = jest.fn();
    const onCancel = jest.fn();

    render(<Subject {...{ onSave, onCancel }} />);

    const nameField = screen.getByLabelText("Public name") as HTMLInputElement;

    await waitFor(() => {
      expect(screen.queryByText("Save")).toBeInTheDocument();
      expect(screen.queryByText("Saving")).not.toBeInTheDocument();
      expect(nameField.value).toEqual(`${mockExperiment!.name} Copy`);
    });

    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalled();

    const saveButton = screen.getByText("Save");

    act(() => void fireEvent.change(nameField, { target: { value: "Oh hi" } }));
    await waitFor(() => expect(saveButton).not.toBeDisabled());

    fireEvent.click(saveButton);
    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
      expect(onSave.mock.calls[0][0]).toEqual({ name: "Oh hi" });
    });
  });

  it("indicates when cloning is in progress", async () => {
    render(<Subject isLoading={true} />);
    await waitFor(() => {
      expect(screen.queryByText("Save")).not.toBeInTheDocument();
      expect(screen.queryByText("Saving")).toBeInTheDocument();
      expect(screen.queryByText("Saving")).toBeDisabled();
    });
  });

  it("keeps the slug in sync with the name field", async () => {
    render(<Subject />);
    const nameField = screen.getByLabelText("Public name");
    const slugField = screen.getByTestId("SlugTextControl") as HTMLInputElement;
    for (const [nameValue, expectedSlug] of [
      ["Hello", "hello"],
      ["Hello world", "hello-world"],
    ]) {
      fireEvent.change(nameField, { target: { value: nameValue } });
      await waitFor(() => {
        expect(slugField.value).toEqual(expectedSlug);
      });
    }
  });
});

type SubjectProps = Partial<React.ComponentProps<typeof CloneDialog>>;

const { experiment: mockExperiment } = mockExperimentQuery("my-special-slug");

const Subject = ({
  show = true,
  experiment = mockExperiment,
  isLoading = false,
  isServerValid = true,
  submitErrors = {},
  setSubmitErrors = () => {},
  onCancel = () => {},
  onSave = () => {},
}: SubjectProps) => (
  <CloneDialog
    {...{
      show,
      experiment,
      isLoading,
      isServerValid,
      submitErrors,
      setSubmitErrors,
      onCancel,
      onSave,
    }}
  />
);
