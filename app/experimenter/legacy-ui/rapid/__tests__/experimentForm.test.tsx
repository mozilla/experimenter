import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import selectEvent from "react-select-event";

import {
  renderWithRouter,
  wrapInExperimentProvider,
} from "experimenter-rapid/__tests__/utils";
import ExperimentForm, {
  SettingsForm,
  BranchesForm,
} from "experimenter-rapid/components/forms/ExperimentForm";
import { INITIAL_CONTEXT } from "experimenter-rapid/contexts/experiment/context";
import {
  ExperimentStatus,
  FirefoxChannel,
} from "experimenter-rapid/types/experiment";
import { ExperimentData } from "experimenter-types/experiment";

afterEach(async () => {
  await cleanup();
  await jest.clearAllMocks();
  await fetchMock.resetMocks();
});

describe("<SettingsForm />", () => {
  it("renders without issues", () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<SettingsForm />),
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
      wrapInExperimentProvider(<SettingsForm />),
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
    const {
      getByText,
      getByLabelText,
      getByTestId,
      history,
      container,
    } = renderWithRouter(wrapInExperimentProvider(<SettingsForm />), {
      route: "/new/",
    });

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

    // Slight hack we'll want to address in `nimbus-ui`: if an XSelect has multiple
    // options, it renders `<div>`s from `react-select` which can't have a `label`
    // since they're not form elements. An `aria-labelledby` works the same, but
    // won't render as an attribute so it's stuck on a container div. Additionally,
    // `data-testid` won't render either so the test goes by ID and not testid.

    // Update the features field
    expect(getByTestId("field-feature-label")).toHaveTextContent("Features");
    const featuresField = container.querySelector(
      "#field-feature",
    ) as HTMLElement;

    await selectEvent.select(featuresField, [
      "Picture-in-Picture",
      "Pinned tabs",
    ]);

    // Update the audience field
    expect(getByTestId("field-audience-label")).toHaveTextContent("Audience");
    const audienceField = container.querySelector(
      "#field-audience",
    ) as HTMLElement;
    await selectEvent.select(audienceField, "US users (en)");

    // Update the firefox version field
    expect(getByTestId("field-firefox-min-version-label")).toHaveTextContent(
      "Firefox Minimum Version",
    );
    const firefoxVersionField = container.querySelector(
      "#field-firefox-min-version",
    ) as HTMLElement;
    await selectEvent.select(firefoxVersionField, "Firefox 78.0");

    // Update the firefox channel field
    expect(getByTestId("field-firefox-channel-label")).toHaveTextContent(
      "Firefox Channel",
    );
    const firefoxChannelField = container.querySelector(
      "#field-firefox-channel",
    ) as HTMLElement;
    await selectEvent.select(firefoxChannelField, "Firefox Nightly");

    // Click the save button
    fireEvent.click(getByText("Save"));

    // Ensure we redirect the user to the details page
    await waitFor(() => expect(historyPush).toHaveBeenCalledTimes(1));
    const lastEntry = history.entries.pop() || { pathname: "" };
    expect(lastEntry.pathname).toBe("/test-slug/");

    // Check the correct data was submitted
    expect(submitUrl).toEqual("/api/v3/experiments/");
    expect(requestMethod).toEqual("POST");
    const expected: ExperimentData = {
      status: ExperimentStatus.DRAFT,
      name: "test name",
      objectives: "test objective",
      features: ["picture_in_picture", "pinned_tabs"],
      audience: "us_only",
      firefox_min_version: "78.0",
      firefox_channel: FirefoxChannel.NIGHTLY,
      variants: [
        {
          name: "control",
          is_control: true,
          description: "An empty branch",
          value: "",
          ratio: 1,
        },
        {
          name: "variant",
          is_control: false,
          description: "An empty branch",
          value: "",
          ratio: 1,
        },
      ],
    };
    expect(formData).toEqual(expected);
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
    } = renderWithRouter(wrapInExperimentProvider(<SettingsForm />), {
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
      status: ExperimentStatus.DRAFT,
      objectives: "Test objectives",
    });
  });

  [
    "name",
    "objectives",
    "features",
    "audience",
    "firefox_min_version",
    "firefox_channel",
  ].forEach((fieldName) => {
    it(`shows the appropriate error message for '${fieldName}' on save`, async () => {
      const { getByText } = renderWithRouter(
        wrapInExperimentProvider(<SettingsForm />),
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
  });
});

describe("<BranchesForm />", () => {
  it("should render the form", async () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<BranchesForm />),
    );
    expect(
      getByText(
        "You can change the configuration of a feature in each branch.",
      ),
    ).toBeInTheDocument();
  });
  it("should render inputs for each variant", async () => {
    const { getByDisplayValue } = renderWithRouter(
      wrapInExperimentProvider(<BranchesForm />),
    );
    const { variants } = INITIAL_CONTEXT.state;
    for (const variant of variants) {
      expect(getByDisplayValue(variant.name)).toBeInTheDocument();
    }
  });

  it("should render a control label", async () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<BranchesForm />),
    );
    // Should only by one control branch
    expect(getByText("control")).toBeInTheDocument();
  });

  it("should have variant fields editable", async () => {
    const { getByDisplayValue, getAllByDisplayValue } = renderWithRouter(
      wrapInExperimentProvider(<BranchesForm />),
    );

    const controlBranch = getByDisplayValue("control");
    const variantBranch = getByDisplayValue("variant");
    const descriptions = getAllByDisplayValue("An empty branch");
    const values = document.querySelectorAll("textarea");

    const controlBranchName = "control branch name";
    fireEvent.change(controlBranch, { target: { value: controlBranchName } });
    expect(getByDisplayValue(controlBranchName)).toBeInTheDocument();

    const controlDescription = "control description";
    fireEvent.change(descriptions[0], {
      target: { value: controlDescription },
    });
    expect(getByDisplayValue(controlDescription)).toBeInTheDocument();

    const controlValue = "[]";
    fireEvent.change(values[0], { target: { value: controlValue } });
    expect(getByDisplayValue(controlValue)).toBeInTheDocument();

    const variantBranchName = "variant branch name";
    fireEvent.change(variantBranch, { target: { value: variantBranchName } });
    expect(getByDisplayValue(variantBranchName)).toBeInTheDocument();

    const variantDescription = "variant description";
    fireEvent.change(descriptions[1], {
      target: { value: variantDescription },
    });
    expect(getByDisplayValue(variantDescription)).toBeInTheDocument();

    const variantValue = "variantValue";
    fireEvent.change(values[0], { target: { value: variantValue } });
    expect(getByDisplayValue(variantValue)).toBeInTheDocument();
  });
});

it("should add and delete branches", async () => {
  const {
    getByText,
    getAllByText,
    queryByDisplayValue,
    getByDisplayValue,
    getAllByDisplayValue,
  } = renderWithRouter(wrapInExperimentProvider(<BranchesForm />));

  fireEvent.click(getByText("Add Branch"));
  expect(getAllByText("Branch")).toHaveLength(3);

  expect(getAllByDisplayValue("33.33")).toHaveLength(3);

  const descriptions = getAllByDisplayValue("An empty branch");

  const changedDescription1 = "gonna be deleted!";
  fireEvent.change(descriptions[1], { target: { value: changedDescription1 } });
  expect(getByDisplayValue(changedDescription1)).toBeInTheDocument();

  const changedDescription2 = "something else!";
  fireEvent.change(descriptions[2], { target: { value: changedDescription2 } });
  expect(getByDisplayValue(changedDescription2)).toBeInTheDocument();

  // delete
  fireEvent.click(getAllByText("×")[0]);

  expect(getAllByText("Branch")).toHaveLength(2);
  expect(queryByDisplayValue(changedDescription1)).toBeNull();
  expect(getAllByDisplayValue("50")).toHaveLength(2);
});

describe("<ExperimentForm />", () => {
  it("should render the settings form by default", () => {
    const { getByText } = renderWithRouter(<ExperimentForm />);
    expect(getByText("Public Name")).toBeInTheDocument();
  });
  it("should render the branches form for /branches route", async () => {
    const { getByText } = renderWithRouter(<ExperimentForm />);

    // Click the branches tab
    fireEvent.click(getByText("Branches"));

    await waitFor(() =>
      expect(
        getByText(
          "You can change the configuration of a feature in each branch.",
        ),
      ).toBeInTheDocument(),
    );
  });
});
