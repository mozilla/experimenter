import { render, act, screen } from "@testing-library/react";
import React from "react";

import ResultsTable from "experimenter-rapid/components/visualization/ResultsTable";
import {
  ExperimentStatus,
  FirefoxChannel,
} from "experimenter-rapid/types/experiment";
import { ExperimentData } from "experimenter-types/experiment";

const EXPERIMENT_DATA: ExperimentData = {
  status: ExperimentStatus.LIVE,
  slug: "test-slug",
  name: "Test Name",
  objectives: "Test objectives",
  owner: "test@owner.com",
  features: ["picture_in_picture"],
  audience: "us_only",
  firefox_channel: FirefoxChannel.RELEASE,
  firefox_min_version: "78.0",
  analysis: {
    show_analysis: true,
    result_map: {
      retained: "binomial",
      search_count: "mean",
      identity: "count",
      picture_in_picture_ever_used: "binomial",
    },
    daily: [],
    weekly: [],
    overall: [
      {
        metric: "picture_in_picture_ever_used",
        statistic: "binomial",
        branch: "control",
        ci_width: 0.95,
        point: 0.05,
        lower: 0.024357271316207685,
        upper: 0.084114637001734827,
      },
      {
        metric: "picture_in_picture_ever_used",
        statistic: "binomial",
        branch: "treatment",
        point: 0.049019607843137254,
        lower: 0.023872203557007872,
        upper: 0.082490692094610241,
      },
      {
        metric: "picture_in_picture_ever_used",
        statistic: "binomial",
        branch: "treatment",
        comparison: "difference",
        point: -0.00065694876288765341,
        upper: 0.043163817365120191,
        lower: 0.041750959639940292,
      },
      {
        metric: "retained",
        statistic: "binomial",
        branch: "control",
        ci_width: 0.95,
        point: 0.92610837438423643,
        lower: 0.88644814975695319,
        upper: 0.95784492649935471,
      },
      {
        metric: "retained",
        statistic: "binomial",
        branch: "treatment",
        point: 0.64215686274509809,
        lower: 0.57529460650836961,
        upper: 0.7063786618426765,
      },
      {
        metric: "retained",
        statistic: "binomial",
        branch: "treatment",
        comparison: "difference",
        point: 0.032060163779913255,
        lower: -0.065023804214299957,
        upper: 0.12483606976999304,
      },
      {
        metric: "search_count",
        statistic: "mean",
        branch: "control",
        ci_width: 0.95,
        point: 14.967359019193298,
        lower: 10.534758870048162,
        upper: 20.754349791764547,
      },
      {
        metric: "search_count",
        statistic: "mean",
        branch: "treatment",
        point: 25.456361412643364,
        lower: 18.998951440573688,
        upper: 33.549291754637153,
      },
      {
        metric: "search_count",
        statistic: "mean",
        branch: "treatment",
        comparison: "difference",
        point: 5.0758527676460012,
        upper: -5.63685604594333,
        lower: -15.289651027022447,
      },
      {
        metric: "identity",
        statistic: "count",
        branch: "control",
        point: 198,
      },
      {
        metric: "identity",
        statistic: "count",
        branch: "treatment",
        point: 200,
      },
      {
        metric: "identity",
        statistic: "percentage",
        branch: "control",
        point: 45,
      },
      {
        metric: "identity",
        statistic: "percentage",
        branch: "treatment",
        point: 55,
      },
    ],
  },
  variants: [],
};

describe("<ResultsTable />", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = [
      "Picture-in-Picture Conversion",
      "2-Week Browser Retention",
      "Daily Mean Searches Per User",
      "Total Users",
    ];

    await act(async () => {
      render(<ResultsTable experimentData={EXPERIMENT_DATA} />);
    });

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has the expected variant and user count", async () => {
    await act(async () => {
      render(<ResultsTable experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
    expect(screen.getByText("198")).toBeInTheDocument();
  });

  it("has correctly labelled result significance", async () => {
    await act(async () => {
      render(<ResultsTable experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.getByTestId("neutral-significance")).toBeInTheDocument();
  });

  it("doesn't show data rows when no data is available", async () => {
    const newData = Object.assign(EXPERIMENT_DATA, { analysis: undefined });
    await act(async () => {
      render(<ResultsTable experimentData={newData} />);
    });

    const rowForTreatmentResults = screen.queryByText("treatment");
    const rowForControlResults = screen.queryByText("control");
    expect(rowForTreatmentResults).toBeNull();
    expect(rowForControlResults).toBeNull();
  });
});
