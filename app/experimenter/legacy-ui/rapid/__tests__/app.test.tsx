import { cleanup, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";

import App from "experimenter-rapid/components/App";

import { renderWithRouter } from "./utils";

afterEach(cleanup);

describe("<App />", () => {
  it("root route shows link to create page", () => {
    const { getByText } = renderWithRouter(<App />);
    expect(getByText("Create a new experiment")).toBeInTheDocument();
  });

  it("unknown route shows 404 message", () => {
    const { getByText } = renderWithRouter(<App />, {
      route: "/a/route/that/does/not/exist/",
    });
    expect(getByText("404")).toBeInTheDocument();
  });

  it("includes the experiment form page at `/new/`", () => {
    const { getByText } = renderWithRouter(<App />, {
      route: "/new/",
    });
    expect(getByText(/Create a New A\/A Experiment/)).toBeInTheDocument();
  });

  it("includes the experiment form page at `/:experimentSlug/edit/`", async () => {
    fetchMock.mockResponse(async () => {
      return JSON.stringify({
        slug: "test-slug",
        name: "Test Name",
        objectives: "Test objectives",
        owner: "test@owner.com",
      });
    });

    const { getByText, getByLabelText } = renderWithRouter(<App />, {
      route: "/test-slug/edit/",
    });
    await waitFor(() => {
      return expect(
        getByText("Edit Experiment: Test Name"),
      ).toBeInTheDocument();
    });

    const nameField = getByLabelText("Public Name") as HTMLInputElement;
    await waitFor(() => {
      return expect(nameField.value).toEqual("Test Name");
    });
  });

  it("includes the experiment details page at `/:experimentSlug/`", async () => {
    fetchMock.mockResponse(async () => {
      return JSON.stringify({
        slug: "test-slug",
        name: "Test Name",
        objectives: "Test objectives",
        owner: "test@owner.com",
        features: ["FEATURE 1", "FEATURE 2"],
        audience: "AUDIENCE 1",
        firefox_min_version: "78.0",
      });
    });

    const { getByText, getAllByText } = renderWithRouter(<App />, {
      route: "/test-slug/",
    });

    await waitFor(() => {
      return expect(getAllByText("Test Name")).toHaveLength(2);
    });
    await waitFor(() => {
      return expect(getByText("test@owner.com")).toBeInTheDocument();
    });
  });
});
