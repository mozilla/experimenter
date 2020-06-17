import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";

import ExperimentForm from "experimenter-rapid/components/forms/ExperimentForm";

afterEach(async () => {
  await cleanup();
  fetchMock.resetMocks();
});

describe("<ExperimentForm />", () => {
  it("renders without issues", () => {
    const { getByText } = render(<ExperimentForm />);
    expect(getByText("Save")).toBeInTheDocument();
  });

  it("makes the correct API call on save", async () => {
    const { getByText, getByLabelText, history } = renderWithRouter(
      <ExperimentForm />,
    );
    let formData;
    fetchMock.mockOnce(async (req) => {
      formData = JSON.parse(req.body);
      return JSON.stringify({ slug: "test-slug" });
    });
    const historyPush = jest.spyOn(history, "push");

    // Update the public name field
    const nameField = getByLabelText("Public Name");
    fireEvent.change(nameField, { target: { value: "test name" } });

    // Update the objectives field
    const objectivesField = getByLabelText("Hypothesis");
    fireEvent.change(objectivesField, { target: { value: "test objective" } });

    // Click the save button
    fireEvent.click(getByText("Save"));

    // Ensure we redirect the user to the details page
    await waitFor(() => expect(historyPush).toHaveBeenCalledTimes(1));
    expect(history.entries.pop().pathname).toBe("/test-slug/");

    // Check the correct data was submitted
    expect(formData).toEqual({
      name: "test name",
      objectives: "test objective",
    });
  });

  it("makes the correct API call on save", async () => {
    const { getByText } = renderWithRouter(<ExperimentForm />);
    let formData;
    fetchMock.mockOnce(async (req) => {
      formData = JSON.parse(req.body);
      return {
        status: 400,
        body: JSON.stringify({ name: ["an error occurred"] }),
      };
    });

    // Click the save button
    fireEvent.click(getByText("Save"));

    // Ensure the error message is shown
    await waitFor(() =>
      expect(getByText("an error occurred")).toBeInTheDocument(),
    );
    expect(formData).toEqual({ name: "", objectives: "" });
  });
});
