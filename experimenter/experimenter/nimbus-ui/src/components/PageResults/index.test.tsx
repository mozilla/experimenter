/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { act } from "react-dom/test-utils";
import PageResults from "src/components/PageResults";
import { ExperimentContextType, RedirectCondition } from "src/lib/contexts";
import { getStatus as mockGetStatus } from "src/lib/experiment";
import { mockExperimentQuery } from "src/lib/mocks";
import {
  MockExperimentContextProvider,
  RouterSlugProvider,
} from "src/lib/test-utils";
import {
  mockAnalysis,
  mockAnalysisWithErrors,
  mockAnalysisWithErrorsAndResults,
  mockAnalysisWithExposures,
  mockAnalysisWithSegments,
  mockAnalysisWithWeeklyExposures,
  MOCK_METADATA_WITH_CONFIG,
} from "src/lib/visualization/mocks";
import { AnalysisData } from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentStatusEnum } from "src/types/globalTypes";

let mockExperiment: getExperiment_experimentBySlug;
let mockAnalysisData: AnalysisData | undefined;

const ENROLLMENTS_BASIS = "enrollments";
const EXPOSURES_BASIS = "exposures";

describe("PageResults", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
  });

  it("renders properly when results are empty", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysis({
          weekly: { enrollments: { all: {} } },
          overall: { enrollments: { all: {} } },
        })}
      />,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
  });

  it("fetches analysis data and displays expected tables when analysis is ready", async () => {
    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("summary")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("table-highlights-overview"),
    ).toBeInTheDocument();
    // length of 2 due to two sets of tabs per table
    expect(screen.queryAllByTestId("table-highlights")).toHaveLength(2);
    expect(screen.queryAllByTestId("table-results")).toHaveLength(2);
    expect(screen.getAllByTestId("table-metric-secondary")).toHaveLength(6);
  });

  it("displays the external config alert when an override exists", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysis({ metadata: MOCK_METADATA_WITH_CONFIG })}
      />,
    );

    await screen.findByTestId("external-config-alert");
  });

  it("displays the analysis_start_time", async () => {
    render(<Subject />);

    expect(
      screen.getByText(
        new Date(MOCK_METADATA_WITH_CONFIG.analysis_start_time).toLocaleString(
          undefined,
          { timeZone: "UTC", timeZoneName: "short" },
        ),
      ),
    );
  });

  it("hides the analysis segment selector when there are no custom segments", async () => {
    render(<Subject />);

    expect(screen.queryByText("Segment")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("segment-results-selector"),
    ).not.toBeInTheDocument();
  });

  it("displays the analysis segment selector and values properly", async () => {
    const { container } = render(
      <Subject mockAnalysisData={mockAnalysisWithSegments} />,
    );

    const defaultSegment = "all";
    const otherSegment = "a_different_segment";

    expect(screen.getByText("Segment"));
    const segmentSelectParent = screen.getByTestId("segment-results-selector");
    expect(within(segmentSelectParent).getByText(defaultSegment));
    expect(
      within(segmentSelectParent).getByTestId(
        `${defaultSegment}-segment-radio`,
      ),
    ).toBeChecked();
    expect(within(segmentSelectParent).getByText(otherSegment));
    expect(
      within(segmentSelectParent).getByTestId(`${otherSegment}-segment-radio`),
    ).not.toBeChecked();

    fireEvent.click(
      within(segmentSelectParent).getByTestId(`${otherSegment}-segment-radio`),
    );
    expect(
      within(segmentSelectParent).getByTestId(
        `${defaultSegment}-segment-radio`,
      ),
    ).not.toBeChecked();
    expect(
      within(segmentSelectParent).getByTestId(`${otherSegment}-segment-radio`),
    ).toBeChecked();
  });

  it("hides the analysis basis selector when there are no exposures", async () => {
    render(<Subject />);

    expect(screen.queryByText("Analysis Basis")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("analysis-basis-results-selector"),
    ).not.toBeInTheDocument();
  });

  it("displays the analysis basis options properly", async () => {
    render(<Subject mockAnalysisData={mockAnalysisWithExposures} />);

    expect(screen.getByText("Analysis Basis"));
    const analysisBasisSelectParent = screen.getByTestId(
      "analysis-basis-results-selector",
    );

    // both exist
    expect(within(analysisBasisSelectParent).getByText(ENROLLMENTS_BASIS));
    expect(within(analysisBasisSelectParent).getByText(EXPOSURES_BASIS));

    // enrollments checked by default
    expect(
      within(analysisBasisSelectParent).getByTestId(
        `${ENROLLMENTS_BASIS}-basis-radio`,
      ),
    ).toBeChecked();

    fireEvent.click(
      within(analysisBasisSelectParent).getByTestId(
        `${EXPOSURES_BASIS}-basis-radio`,
      ),
    );

    // exposures checked after click
    expect(
      within(analysisBasisSelectParent).getByTestId(
        `${EXPOSURES_BASIS}-basis-radio`,
      ),
    ).toBeChecked();
  });

  it("displays the analysis basis options for weekly results", async () => {
    render(<Subject mockAnalysisData={mockAnalysisWithWeeklyExposures} />);

    expect(screen.getByText("Analysis Basis"));
    const analysisBasisSelectParent = screen.getByTestId(
      "analysis-basis-results-selector",
    );

    // both exist
    expect(within(analysisBasisSelectParent).getByText(ENROLLMENTS_BASIS));
    expect(within(analysisBasisSelectParent).getByText(EXPOSURES_BASIS));
  });

  it("displays analysis errors", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysisWithErrors()}
        mockExperiment={
          mockExperimentQuery("demo-slug", {
            status: NimbusExperimentStatusEnum.COMPLETE,
            showResultsUrl: true,
          }).experiment
        }
      />,
    );

    expect(screen.getByText("NoEnrollmentPeriodException"));
    expect(
      screen.getByText(
        "Error while computing statistic bootstrap_mean for metric picture_in_picture",
        { exact: false },
      ),
    );
    expect(
      screen.getByText(
        "Error while computing statistic bootstrap_mean for metric feature_b",
        { exact: false },
      ),
    );
    expect(screen.getAllByTestId("analysis-error")).toHaveLength(3);
  });

  it("displays analysis errors if no results exist for metric, else results", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysisWithErrorsAndResults()}
        mockExperiment={
          mockExperimentQuery("demo-slug", {
            status: NimbusExperimentStatusEnum.COMPLETE,
            showResultsUrl: true,
          }).experiment
        }
      />,
    );

    expect(
      screen.getByText(
        "Error while computing statistic bootstrap_mean for metric picture_in_picture",
        { exact: false },
      ),
    );
    expect(
      screen.queryByText(
        "Error while computing statistic bootstrap_mean for metric feature_b",
        { exact: false },
      ),
    ).toBeNull();
  });

  it("displays no results message when other metrics have errors", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysisWithErrors()}
        mockExperiment={
          mockExperimentQuery("demo-slug", {
            status: NimbusExperimentStatusEnum.COMPLETE,
            showResultsUrl: true,
          }).experiment
        }
      />,
    );

    expect(
      screen.getAllByText(
        "StatisticComputationException calculating bootstrap_mean",
      ),
    );
    expect(
      screen.getAllByText("No results available for metric."),
    ).toHaveLength(3);
  });

  it("displays errors for metrics that do not appear in data or outcomes", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysis({
          errors: {
            experiment: [],
            bad_metric: [
              {
                exception:
                  "(<class 'jetstream.errors.BadThingException'>, BadThingException('Error while computing statistic test_statistic for metric bad_metric: UH OH'), None)",
                exception_type: "BadThingException",
                experiment: "demo-slug",
                filename: "statistics.py",
                func_name: "apply",
                log_level: "ERROR",
                message:
                  "Error while computing statistic test_statistic for metric bad_metric: UH OH",
                metric: "bad_metric",
                statistic: "test_statistic",
                timestamp: "2022-11-04 00:00:00+00:00",
                analysis_basis: "enrollments",
                segment: "all",
              },
            ],
          },
        })}
        mockExperiment={
          mockExperimentQuery("demo-slug", {
            status: NimbusExperimentStatusEnum.COMPLETE,
            showResultsUrl: true,
          }).experiment
        }
      />,
    );

    expect(screen.getByText("Other Metric Errors"));

    expect(screen.getByText("BadThingException calculating test_statistic"));

    expect(
      screen.getByText(
        "Error while computing statistic test_statistic for metric bad_metric",
        { exact: false },
      ),
    );
  });

  it("redirects to the edit overview page if the experiment status is draft", async () => {
    expect(
      redirectTestCommon({
        mockExperiment: mockExperimentQuery("demo-slug", {
          status: NimbusExperimentStatusEnum.DRAFT,
        }).experiment,
      }),
    ).toEqual("edit/overview");
  });

  it("redirects to the summary page if the visualization flag is set to false", async () => {
    expect(
      redirectTestCommon({
        mockAnalysisData: mockAnalysis({ show_analysis: false }),
        mockExperiment: mockExperimentQuery("demo-slug", {
          status: NimbusExperimentStatusEnum.COMPLETE,
          showResultsUrl: true,
        }).experiment,
      }),
    ).toEqual("");
  });

  it("redirects to the summary page if the visualization results are not ready", async () => {
    expect(
      redirectTestCommon({
        mockExperiment: mockExperimentQuery("demo-slug", {
          status: NimbusExperimentStatusEnum.COMPLETE,
        }).experiment,
      }),
    ).toEqual("");
  });

  const redirectTestCommon = (props: React.ComponentProps<typeof Subject>) => {
    const { mockAnalysisData, mockExperiment } = props;
    const useRedirectCondition = jest.fn();
    render(
      <Subject
        {...{
          ...props,
          context: {
            useRedirectCondition,
          },
        }}
      />,
    );
    expect(useRedirectCondition).toHaveBeenCalled();
    const condition = useRedirectCondition.mock
      .calls[0][0] as RedirectCondition;
    return condition({
      analysis: mockAnalysisData,
      status: mockGetStatus(mockExperiment),
    });
  };

  it("displays grouped metrics via onClick", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText("Hide other metrics"));
    });
    expect(screen.getByText("Show other metrics")).toBeInTheDocument();
  });
});

const Subject = ({
  mockExperiment = mockExperimentQuery("demo-slug", { showResultsUrl: true })
    .experiment,
  mockAnalysisData = mockAnalysis(),
  context = {},
}: {
  mockExperiment?: getExperiment_experimentBySlug;
  mockAnalysisData?: AnalysisData | undefined;
  context?: Partial<ExperimentContextType>;
}) => (
  <RouterSlugProvider>
    <MockExperimentContextProvider
      value={{
        experiment: mockExperiment,
        analysis: mockAnalysisData,
        status: mockGetStatus(mockExperiment),
        analysisRequired: true,
        ...context,
      }}
    >
      <PageResults />
    </MockExperimentContextProvider>
  </RouterSlugProvider>
);
