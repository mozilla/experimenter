/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import {
  createHistory,
  createMemorySource,
  History,
  LocationProvider,
  navigate,
  RouteComponentProps,
  Router,
} from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React, { useContext, useRef, useState } from "react";
import ExperimentRoot from ".";
import { BASE_PATH, POLL_INTERVAL } from "../../../lib/constants";
import { ExperimentContext } from "../../../lib/contexts";
import { MockedCache, mockExperimentQuery } from "../../../lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../../types/globalTypes";

describe("ExperimentRoot", () => {
  const MOCK_ANALYSIS_DATA = JSON.stringify({ fake: "data" });

  beforeAll(() => {
    fetchMock.enableMocks();
    fetchMock.mockResponse(async (req) => {
      if (req.url.startsWith("/api/v3/visualization/")) {
        return new Promise((resolve) =>
          setTimeout(() => resolve(MOCK_ANALYSIS_DATA), 100),
        );
      } else {
        throw new Error("unexpected URL");
      }
    });
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  it("produces an ExperimentContext as expected", async () => {
    const slug = "experiment-demo-slug";
    const { mock, experiment } = mockExperimentQuery(slug);

    const SubjectInner = (props: RouteComponentProps) => {
      const { slug, experiment } = useContext(ExperimentContext)!;
      return (
        <div data-testid="SubjectInner">
          <ul>
            <li data-testid="id">{experiment.id}</li>
            <li data-testid="slug">{slug}</li>
          </ul>
        </div>
      );
    };

    render(
      <Subject {...{ slug, mocks: [mock] }}>
        <SubjectInner path="edit" />
      </Subject>,
    );

    await screen.findByTestId("SubjectInner");
    expect(screen.getByTestId("id")).toHaveTextContent(String(experiment.id));
    expect(screen.getByTestId("slug")).toHaveTextContent(slug);
  });

  const AnalysisSubjectInner = (props: RouteComponentProps) => {
    const { experiment, analysis, analysisLoading, analysisRequired } =
      useContext(ExperimentContext)!;
    // Super-hacky way to track whether or not we ever rendered while
    // analysis was loading.
    const analysisLoadingRenders = useRef(0);
    if (analysisLoading) analysisLoadingRenders.current++;
    return (
      <div data-testid="SubjectInner">
        <ul>
          <li data-testid="id">{experiment.id}</li>
          <li data-testid="analysisLoading">{"" + analysisLoading}</li>
          <li data-testid="analysisLoadingRenders">
            {"" + analysisLoadingRenders.current}
          </li>
          <li data-testid="analysisRequired">{"" + analysisRequired}</li>
          <li data-testid="analysis">{JSON.stringify(analysis)}</li>
        </ul>
      </div>
    );
  };

  it("fetches analysis data for live experiments", async () => {
    const slug = "experiment-demo-slug";
    const { mock } = mockExperimentQuery(slug, {
      status: NimbusExperimentStatusEnum.LIVE,
    });

    render(
      <Subject {...{ slug, mocks: [mock] }}>
        <AnalysisSubjectInner path="edit" />
      </Subject>,
    );

    // Loading experiment...
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
    // Experiment loaded, fetching analysis...
    await waitFor(() => {
      expect(screen.queryByTestId("page-loading")).not.toBeInTheDocument();
      expect(screen.getByTestId("analysisLoading")).toHaveTextContent("true");
    });
    // Analysis fetch initiated...
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    // Analysis response received...
    await waitFor(() => {
      expect(screen.getByTestId("analysisLoading")).toHaveTextContent("false");
      expect(screen.getByTestId("analysis")).toHaveTextContent(
        MOCK_ANALYSIS_DATA,
      );
    });
    // Should have rendered at least once while analysis was loading, because
    // this component didn't require analysis
    expect(screen.getByTestId("analysisLoadingRenders")).not.toHaveTextContent(
      "0",
    );
  });

  it("supplies a useAnalysisRequired hook that indicates when to wait for analysis fetch", async () => {
    const slug = "experiment-demo-slug";
    const { mock } = mockExperimentQuery(slug, {
      status: NimbusExperimentStatusEnum.LIVE,
    });

    const AnalysisRequiredSubjectInner = (props: RouteComponentProps) => {
      const { useAnalysisRequired } = useContext(ExperimentContext)!;
      useAnalysisRequired();
      return <AnalysisSubjectInner />;
    };

    render(
      <Subject {...{ slug, mocks: [mock] }}>
        <AnalysisRequiredSubjectInner path="edit" />
      </Subject>,
    );

    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByTestId("page-loading")).not.toBeInTheDocument();
      expect(screen.getByTestId("analysisLoading")).toHaveTextContent("false");
    });
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByTestId("analysis")).toHaveTextContent(
        MOCK_ANALYSIS_DATA,
      );
    });
    // Should have never rendered while analysis was loading, because the
    // global page spinner should have stayed up.
    expect(screen.getByTestId("analysisLoadingRenders")).toHaveTextContent("0");
  });

  it("supplies a useRedirectCondition hook that enables redirection based on experiment conditions", async () => {
    const slug = "experiment-demo-slug";
    const { mock, experiment } = mockExperimentQuery(slug, {
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
    });

    const SubjectInner = (props: RouteComponentProps) => {
      const { useRedirectCondition } = useContext(ExperimentContext)!;
      useRedirectCondition(({ status }) => {
        if (status.review) return "";
      });
      return <div data-testid="SubjectInner">Redirecting...</div>;
    };

    render(
      <Subject {...{ slug, mocks: [mock] }}>
        <SubjectInner path="edit" />
      </Subject>,
    );

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(`${BASE_PATH}/${experiment.slug}`, {
        replace: true,
      });
    });
  });

  it("supplies a useExperimentPolling hook that enables experiment polling", async () => {
    jest.useFakeTimers();

    const slug = "experiment-demo-slug";
    const { mock: initialMock, experiment: initialExperiment } =
      mockExperimentQuery(slug);
    const { mock: updatedMock, experiment: updatedExperiment } =
      mockExperimentQuery(slug, {
        publishStatus: NimbusExperimentPublishStatusEnum.WAITING,
      });
    const { mock: ignoredMock, experiment: ignoredExperiment } =
      mockExperimentQuery(slug, {
        publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      });

    const SubjectInner = (props: RouteComponentProps) => {
      const {
        experiment: { publishStatus },
      } = useContext(ExperimentContext)!;
      const [enablePolling, setEnablePolling] = useState(false);
      return (
        <div data-testid="SubjectInner">
          <ul>
            <li data-testid="publishStatus">{publishStatus}</li>
          </ul>
          <button
            data-testid="toggle-polling"
            onClick={() => setEnablePolling((state) => !state)}
          >
            Toggle Polling
          </button>
          {enablePolling && <SubjectPollingEnabler />}
        </div>
      );
    };

    const SubjectPollingEnabler = () => {
      const { useExperimentPolling } = useContext(ExperimentContext)!;
      useExperimentPolling();
      return <div data-testid="polling-enabled">Polling enabled</div>;
    };

    render(
      <Subject {...{ slug, mocks: [initialMock, updatedMock, ignoredMock] }}>
        <SubjectInner path="edit" />
      </Subject>,
    );

    await screen.findByTestId("SubjectInner");
    expect(screen.getByTestId("publishStatus")).toHaveTextContent(
      initialExperiment!.publishStatus!,
    );

    // Toggling polling on should introduce SubjectPollingEnabler into the
    // DOM and call useExperimentPolling as a side-effect, enabling polling.
    fireEvent.click(screen.getByTestId("toggle-polling"));
    await waitFor(() => {
      expect(screen.queryByTestId("polling-enabled")).toBeInTheDocument();
    });

    // Travel forward in time and assert that polling fetched the update
    jest.advanceTimersByTime(POLL_INTERVAL);
    await waitFor(() => {
      expect(screen.getByTestId("publishStatus")).toHaveTextContent(
        updatedExperiment!.publishStatus!,
      );
    });

    // Toggling polling off should trigger the cleanup handler of
    // useExperimentPolling and disable polling
    fireEvent.click(screen.getByTestId("toggle-polling"));
    await waitFor(() => {
      expect(screen.queryByTestId("polling-enabled")).not.toBeInTheDocument();
    });

    // Travel forward in time and assert that polling did not fetch again
    jest.advanceTimersByTime(POLL_INTERVAL * 2);
    await waitFor(() => {
      expect(screen.getByTestId("publishStatus")).not.toHaveTextContent(
        ignoredExperiment!.publishStatus!,
      );
    });
  });
});

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

const Subject = ({
  slug = "demo-slug",
  path = `${BASE_PATH}/${slug}/edit`,
  mocks = [],
  history = createHistory(createMemorySource(path)),
  children,
}: {
  slug?: string;
  routePath?: string;
  path?: string;
  mocks?: MockedResponse<Record<string, any>>[];
  history?: History;
  children: React.ReactNode;
}) => {
  return (
    <MockedCache {...{ mocks }}>
      <LocationProvider {...{ history }}>
        <Router basepath={BASE_PATH}>
          <ExperimentRoot path=":slug">{children}</ExperimentRoot>
        </Router>
      </LocationProvider>
    </MockedCache>
  );
};
