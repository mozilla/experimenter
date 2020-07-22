import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";

import {
  renderWithRouter,
  wrapInExperimentProvider,
} from "experimenter-rapid/__tests__/utils";
import ExperimentDetails from "experimenter-rapid/components/experiments/ExperimentDetails";
import { ExperimentStatus } from "experimenter-types/experiment";

afterEach(async () => {
  await cleanup();
  fetchMock.resetMocks();
});

describe("<ExperimentDetails />", () => {
  it("renders without issues", async () => {
    const { getByDisplayValue } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentDetails />, {
        initialState: {
          status: ExperimentStatus.DRAFT,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["picture_in_picture", "pinned_tabs"],
          audience: "us_only",
          firefox_min_version: "78.0",
        },
      }),
    );

    await waitFor(() => {
      return expect(getByDisplayValue("test@owner.com")).toBeInTheDocument();
    });

    expect(getByDisplayValue("Test Name")).toBeInTheDocument();
    expect(getByDisplayValue("Test objectives")).toBeInTheDocument();
  });

  it("renders with bugzilla info when data provided", async () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentDetails />, {
        initialState: {
          status: ExperimentStatus.DRAFT,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["picture_in_picture", "pinned_tabs"],
          audience: "us_only",
          firefox_min_version: "78.0",
          bugzilla_url: "https://example.com",
        },
      }),
    );

    await waitFor(() => {
      return expect(getByText(/Bugzilla ticket/)).toBeInTheDocument();
    });
  });

  it("renders without bugzilla info when data missing", async () => {
    const { getByDisplayValue, queryByText } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentDetails />, {
        initialState: {
          status: ExperimentStatus.DRAFT,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["pinned_tabs", "picture_in_picture"],
          audience: "all_english",
          firefox_min_version: "78.0",
        },
      }),
    );

    await waitFor(() => {
      return expect(getByDisplayValue("test@owner.com")).toBeInTheDocument();
    });

    expect(queryByText(/Bugzilla ticket/)).toBe(null);
  });

  it("sends you to the edit page when the 'Back' button is clicked", async () => {
    const { getByText, history } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentDetails />, {
        initialState: {
          status: ExperimentStatus.DRAFT,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["picture_in_picture", "pinned_tabs"],
          audience: "us_only",
          firefox_min_version: "78.0",
        },
      }),
    );

    const historyPush = jest.spyOn(history, "push");

    const backButton = getByText("Back");
    fireEvent.click(backButton);

    await waitFor(() => expect(historyPush).toHaveBeenCalledTimes(1));
    const lastEntry = history.entries.pop() || { pathname: "" };
    expect(lastEntry.pathname).toBe("/test-slug/edit/");
  });

  it("sends POST to request_review API endpoint when 'Request Approval' button is clicked", async () => {
    const { getByText } = renderWithRouter(
      wrapInExperimentProvider(<ExperimentDetails />, {
        initialState: {
          status: ExperimentStatus.DRAFT,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["picture_in_picture", "pinned_tabs"],
          audience: "us_only",
          firefox_min_version: "78.0",
        },
      }),
    );

    let submitUrl;
    let requestMethod;
    fetchMock.mockOnce(async (req) => {
      requestMethod = req.method;
      submitUrl = req.url;

      return JSON.stringify({ status: "Review" });
    });

    // Click the review button
    fireEvent.click(getByText("Request Approval"));

    // Check the correct data was submitted
    expect(submitUrl).toEqual("/api/v3/experiments/test-slug/request_review/");
    expect(requestMethod).toEqual("POST");
  });
});
