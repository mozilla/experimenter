import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import selectEvent from "react-select-event";

import {
  renderWithRouter,
  wrapInExperimentProvider,
} from "experimenter-rapid/__tests__/utils";
import ExperimentForm from "experimenter-rapid/components/forms/ExperimentForm";
import { ExperimentStatus } from "experimenter-rapid/types/experiment";

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

    // Update the features field
    const featuresField = getByLabelText("Features");
    await selectEvent.select(featuresField, ["FEATURE 1", "FEATURE 2"]);

    // Update the audience field
    const audienceField = getByLabelText("Audience");
    await selectEvent.select(audienceField, "AUDIENCE 2");

    // Update the firefox version field
    const firefoxVersionField = getByLabelText("Firefox Minimum Version");
    await selectEvent.select(firefoxVersionField, "Firefox 78.0");

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
      status: ExperimentStatus.DRAFT,
      name: "test name",
      objectives: "test objective",
      audience: "AUDIENCE 2",
      features: ["FEATURE 1", "FEATURE 2"],
      firefox_min_version: "78.0",
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

  ["name", "objectives", "features", "audience", "firefox_min_version"].forEach(
    (fieldName) => {
      it(`shows the appropriate error message for '${fieldName}' on save`, async () => {
        const { getByText } = renderWithRouter(
          wrapInExperimentProvider(<ExperimentForm />),
        );
        fetchMock.mockOnce(async () => {
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
