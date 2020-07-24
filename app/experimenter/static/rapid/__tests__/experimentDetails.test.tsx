import { cleanup, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { act } from "react-dom/test-utils";

import {
  renderWithRouter,
  wrapInExperimentProvider,
} from "experimenter-rapid/__tests__/utils";
import ExperimentDetails, {
  POLL_TIMEOUT,
} from "experimenter-rapid/components/experiments/ExperimentDetails";
import { ExperimentStatus } from "experimenter-types/experiment";

describe("<ExperimentDetails />", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(async () => {
    await cleanup();
    fetchMock.resetMocks();
  });

  it("renders without issues", async () => {
    await act(async () => {
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
  });

  it("polls fetchExperiment after timeout", async () => {
    await act(async () => {
      fetchMock.mockOnce(async () => {
        return JSON.stringify({
          status: ExperimentStatus.REVIEW,
          slug: "test-slug",
          name: "Test Name",
          objectives: "Test objectives",
          owner: "test@owner.com",
          features: ["FEATURE 1", "FEATURE 2"],
          audience: "AUDIENCE 1",
          firefox_min_version: "78.0",
        });
      });

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

      await waitFor(() => {
        return expect(getByText(ExperimentStatus.DRAFT)).toBeInTheDocument();
      });

      jest.advanceTimersByTime(POLL_TIMEOUT);

      await waitFor(() => {
        return expect(getByText(ExperimentStatus.REVIEW)).toBeInTheDocument();
      });
    });
  });

  it("renders without progression buttons post launched experiments", async () => {
    await act(async () => {
      const { getByDisplayValue, queryByText } = renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            status: ExperimentStatus.LIVE,
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

      expect(queryByText("Back")).toBe(null);
      expect(queryByText("Request Approval")).toBe(null);
    });
  });

  it("renders with bugzilla info when data provided", async () => {
    await act(async () => {
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
  });

  it("renders without bugzilla info when data missing", async () => {
    await act(async () => {
      const { queryByText } = renderWithRouter(
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

      expect(queryByText(/Bugzilla ticket/)).toBe(null);
    });
  });

  it("renders with monitoring link when data provided", async () => {
    await act(async () => {
      const { getByText } = renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            audience: "us_only",
            bugzilla_url: "https://example.com",
            features: ["picture_in_picture", "pinned_tabs"],
            firefox_min_version: "78.0",
            monitoring_dashboard_url: "https://example.com/dashboard",
            name: "Test Name",
            objectives: "Test objectives",
            owner: "test@owner.com",
            slug: "test-slug",
            status: ExperimentStatus.DRAFT,
          },
        }),
      );

      await waitFor(() => {
        return expect(getByText(/monitoring dashboard/)).toBeInTheDocument();
      });
    });
  });

  it("renders without monitoring link when data missing", async () => {
    await act(async () => {
      const { queryByText } = renderWithRouter(
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

      expect(queryByText(/monitoring dashboard/)).toBe(null);
    });
  });

  it("sends you to the edit page when the 'Back' button is clicked", async () => {
    await act(async () => {
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
  });

  it("sends POST to request_review API endpoint when 'Request Approval' button is clicked", async () => {
    await act(async () => {
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

      fetchMock.mockResponse(async () =>
        JSON.stringify({
          status: ExperimentStatus.REVIEW,
        }),
      );

      // Click the review button
      fireEvent.click(getByText("Request Approval"));

      expect(fetch).toBeCalledWith(
        "/api/v3/experiments/test-slug/request_review/",
        {
          method: "POST",
        },
      );
    });
  });
});
