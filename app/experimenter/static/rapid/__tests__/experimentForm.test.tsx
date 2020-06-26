import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";

import {
  renderWithRouter,
  wrapInExperimentProvider,
} from "experimenter-rapid/__tests__/utils";
import ExperimentForm from "experimenter-rapid/components/forms/ExperimentForm";

afterEach(async () => {
  await cleanup();
  fetchMock.resetMocks();
});

describe("<ExperimentForm />", () => {
  it("renders without issues", () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentForm />),
    );
    expect(getByText("Save")).toBeInTheDocument();
  });

  it("is populated when data is available", async () => {
    fetchMock.mockOnce(async () => {
      return JSON.stringify({
        slug: "test-slug",
        name: "Test Name",
        objectives: "Test objectives",
        owner: "test@owner.com",
      });
    });

    const { getByLabelText } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentForm />),
      {
        route: "/test-slug/edit/",
        matchRoutePath: "/:experimentSlug/edit/",
      },
    );

    const nameField = getByLabelText("Public Name") as HTMLInputElement;
    await waitFor(() => {
      return expect(nameField.value).toEqual("Test Name");
    });

    const objectivesField = getByLabelText("Hypothesis") as HTMLInputElement;
    expect(objectivesField.value).toEqual("Test objectives");
  });

  it("makes the correct API call on save new", async () => {
    const { getByText, getByLabelText, history } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentForm />),
      {
        route: "/new/",
      },
    );

    let submitUrl;
    let formData;
    let requestMethod;
    fetchMock.mockOnce(async (req) => {
      if (req.body) {
        formData = await req.json();
      }

      requestMethod = req.method;
      submitUrl = req.url;

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
    const lastEntry = history.entries.pop() || { pathname: "" };
    expect(lastEntry.pathname).toBe("/test-slug/");

    // Check the correct data was submitted
    expect(submitUrl).toEqual("/api/v3/experiments/");
    expect(requestMethod).toEqual("POST");
    expect(formData).toEqual({
      name: "test name",
      objectives: "test objective",
    });
  });

  it("makes the correct API call on save existing", async () => {
    fetchMock.mockOnce(async () => {
      return JSON.stringify({
        name: "Test Name",
        objectives: "Test objectives",
      });
    });

    const {
      getByText,
      getByLabelText,
      getByDisplayValue,
      history,
    } = renderWithRouter(wrapInExperimentProvider(<ExperimentForm />), {
      route: "/test-slug/edit/",
      matchRoutePath: "/:experimentSlug/edit/",
    });

    await waitFor(() =>
      expect(getByDisplayValue("Test Name")).toBeInTheDocument(),
    );

    let submitUrl;
    let formData;
    let requestMethod;
    fetchMock.mockOnce(async (req) => {
      if (req.body) {
        formData = await req.json();
      }

      requestMethod = req.method;
      submitUrl = req.url;

      return JSON.stringify({ slug: "test-slug" });
    });
    const historyPush = jest.spyOn(history, "push");

    // Update the public name field
    const nameField = getByLabelText("Public Name");
    fireEvent.change(nameField, { target: { value: "foo" } });

    // Click the save button
    fireEvent.click(getByText("Save"));

    // Ensure we redirect the user to the details page
    await waitFor(() => expect(historyPush).toHaveBeenCalledTimes(1));
    const lastEntry = history.entries.pop() || { pathname: "" };
    expect(lastEntry.pathname).toBe("/test-slug/");

    // Check the correct data was submitted
    expect(submitUrl).toEqual("/api/v3/experiments/test-slug/");
    expect(requestMethod).toEqual("PUT");
    expect(formData).toEqual({
      name: "foo",
      objectives: "Test objectives",
    });
  });

  ["name", "objectives", "feature", "audience", "trigger", "version"].forEach(
    (fieldName) => {
      it(`shows the appropriate error message for '${fieldName}' on save`, async () => {
        const { getByText } = renderWithRouter(
          wrapInExperimentProvider(<ExperimentForm />),
        );
        fetchMock.mockOnce(async (req) => {
          return {
            status: 400,
            body: JSON.stringify({ [fieldName]: ["an error occurred"] }),
          };
        });

        // Click the save button
        fireEvent.click(getByText("Save"));

        // Ensure the error message is shown
        await waitFor(() =>
          expect(getByText("an error occurred")).toBeInTheDocument(),
        );
      });
    },
  );
});
