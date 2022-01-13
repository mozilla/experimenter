/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { act } from "react-dom/test-utils";
import PageResults from ".";
import { ExperimentContextType, RedirectCondition } from "../../lib/contexts";
import { getStatus as mockGetStatus } from "../../lib/experiment";
import { mockExperimentQuery } from "../../lib/mocks";
import {
  MockExperimentContextProvider,
  RouterSlugProvider,
} from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
  MOCK_UNAVAILABLE_ANALYSIS,
} from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentStatusEnum } from "../../types/globalTypes";

let mockExperiment: getExperiment_experimentBySlug;
let mockAnalysisData: AnalysisData | undefined;

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
    expect(screen.getAllByTestId("table-metric-secondary")).toHaveLength(4);
  });

  it("displays the external config alert when an override exists", async () => {
    render(
      <Subject
        mockAnalysisData={mockAnalysis({ metadata: MOCK_METADATA_WITH_CONFIG })}
      />,
    );

    await screen.findByTestId("external-config-alert");
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
        }).experiment,
      }),
    ).toEqual("");
  });

  it("redirects to the summary page if the visualization results are not ready", async () => {
    expect(
      redirectTestCommon({
        mockAnalysisData: MOCK_UNAVAILABLE_ANALYSIS,
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

  xit("displays grouped metrics via onClick", async () => {
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
  mockExperiment = mockExperimentQuery("demo-slug").experiment,
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
