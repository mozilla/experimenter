import { render, act, screen } from "@testing-library/react";
import React from "react";

import { EXPERIMENT_DATA } from "experimenter-rapid/__tests__/visualizationTestData";
import PrimaryMetricTable from "experimenter-rapid/components/visualization/PrimaryMetricTable";

const PROBESET_A = "picture_in_picture";
const PROBESET_B = "feature_b";
const PROBESET_C = "feature_c";

describe("<PrimaryMetricTable />", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = [
      "Conversions / Total Users",
      "Conversion Rate",
      "Relative Improvement",
    ];
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_A}
        />,
      );
    });

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has correctly labelled result significance", async () => {
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_A}
        />,
      );
    });

    const negativeSignificance = screen.queryByTestId("negative-significance");
    const neutralSignificance = screen.queryByTestId("neutral-significance");

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(negativeSignificance).not.toBeInTheDocument();
    expect(neutralSignificance).not.toBeInTheDocument();
  });

  it("has the expected control and treatment labels", async () => {
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_A}
        />,
      );
    });

    expect(screen.getAllByText("control")).toHaveLength(2);
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("shows the positive improvement bar", async () => {
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_A}
        />,
      );
    });

    const negativeBlock = screen.queryByTestId("negative-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("positive-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("shows the negative improvement bar", async () => {
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_B}
        />,
      );
    });

    const positiveBlock = screen.queryByTestId("positive-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("negative-block")).toBeInTheDocument();
    expect(positiveBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("shows the neutral improvement bar", async () => {
    await act(async () => {
      render(
        <PrimaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_C}
        />,
      );
    });

    const negativeBlock = screen.queryByTestId("negative-block");
    const positiveBlock = screen.queryByTestId("positive-block");

    expect(screen.getByTestId("neutral-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(positiveBlock).not.toBeInTheDocument();
  });

  it("doesn't show data rows when no data is available", async () => {
    const newData = Object.assign(EXPERIMENT_DATA, { analysis: undefined });
    await act(async () => {
      render(
        <PrimaryMetricTable experimentData={newData} probeset={PROBESET_A} />,
      );
    });

    const rowForTreatmentResults = screen.queryByText("treatment");
    const rowForControlResults = screen.queryByText("control");
    expect(rowForTreatmentResults).not.toBeInTheDocument();
    expect(rowForControlResults).not.toBeInTheDocument();
  });
});
