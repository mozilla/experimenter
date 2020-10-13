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
import {
  ExperimentStatus,
  FirefoxChannel,
} from "experimenter-rapid/types/experiment";

describe("<ExperimentDetails />", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(async () => {
    await cleanup();
    fetchMock.resetMocks();
  });

  it("renders in DRAFT state", async () => {
    await act(async () => {
      const { getByText, getAllByText } = renderWithRouter(
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
            firefox_channel: FirefoxChannel.NIGHTLY,
            variants: [],
          },
        }),
      );

      await waitFor(() => {
        return expect(getByText("test@owner.com")).toBeInTheDocument();
      });

      expect(getAllByText("Test Name")).toHaveLength(2);
      expect(getByText("Test objectives")).toBeInTheDocument();
    });
  });

  it("renders in LIVE state", async () => {
    await act(async () => {
      const { getByText, queryByText } = renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            status: ExperimentStatus.LIVE,
            slug: "test-slug",
            recipe_slug: "bug-123-test-slug",
            name: "Test Name",
            objectives: "Test objectives",
            owner: "test@owner.com",
            features: ["picture_in_picture", "pinned_tabs"],
            audience: "us_only",
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      await waitFor(() => {
        return expect(getByText("test@owner.com")).toBeInTheDocument();
      });

      expect(getByText("bug-123-test-slug")).toBeInTheDocument();
      expect(queryByText("Back")).toBe(null);
      expect(queryByText("Request Approval")).toBe(null);
    });
  });

  it("renders in REJECTED state", async () => {
    await act(async () => {
      const { getByText } = renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            status: ExperimentStatus.REJECTED,
            slug: "test-slug",
            name: "Test Name",
            objectives: "Test objectives",
            owner: "test@owner.com",
            features: ["picture_in_picture", "pinned_tabs"],
            audience: "us_only",
            firefox_min_version: "78.0",
            firefox_channel: FirefoxChannel.RELEASE,
            reject_feedback: {
              changed_on: "2020-07-30T05:37:22.540985Z",
              message: "It's no good",
            },
            variants: [],
          },
        }),
      );

      await waitFor(() => {
        return expect(getByText("test@owner.com")).toBeInTheDocument();
      });

      expect(getByText("Review Feedback")).toBeInTheDocument();
      expect(getByText("Reject reason: It's no good")).toBeInTheDocument();

      expect(getByText("Back")).not.toHaveAttribute("disabled");
      expect(getByText("Request Approval")).toHaveAttribute("disabled");
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
            firefox_channel: FirefoxChannel.RELEASE,
            bugzilla_url: "https://example.com",
            variants: [],
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      expect(queryByText(/Bugzilla ticket/)).toBe(null);
    });
  });

  it("renders without recipe_slug when data missing", async () => {
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      expect(queryByText(/Experiment slug/)).toBe(null);
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
            firefox_channel: FirefoxChannel.RELEASE,
            status: ExperimentStatus.DRAFT,
            variants: [],
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      expect(queryByText(/monitoring dashboard/)).toBe(null);
    });
  });

  it("renders with analysis report when live", async () => {
    await act(async () => {
      const { getByText } = renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            status: ExperimentStatus.LIVE,
            recipe_slug: "test-slug",
            name: "Test Name",
            objectives: "Test objectives",
            owner: "test@owner.com",
            features: ["pinned_tabs", "picture_in_picture"],
            audience: "all_english",
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      expect(getByText(/The results can be found/)).toBeInTheDocument();
    });
  });

  it("renders without analysis report when not live", async () => {
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
          },
        }),
      );

      expect(queryByText(/The results can be found/)).toBe(null);
    });
  });

  it("Initializes the svelte code as expected", async () => {
    window.initSvelte = () => {
      return;
    };

    await act(async () => {
      renderWithRouter(
        wrapInExperimentProvider(<ExperimentDetails />, {
          initialState: {
            status: ExperimentStatus.LIVE,
            slug: "test-slug",
            recipe_slug: "bug-123-test-slug",
            name: "Test Name",
            objectives: "Test objectives",
            owner: "test@owner.com",
            features: ["picture_in_picture", "pinned_tabs"],
            audience: "us_only",
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            analysis: {
              show_analysis: true,
              daily: [],
              weekly: [],
              overall: {},
            },
            variants: [],
          },
        }),
      );
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
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

  it("polls fetchExperiment after timeout", async () => {
    await act(async () => {
      fetchMock.mockResponse(async () => {
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
            firefox_channel: FirefoxChannel.RELEASE,
            firefox_min_version: "78.0",
            variants: [],
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
});
