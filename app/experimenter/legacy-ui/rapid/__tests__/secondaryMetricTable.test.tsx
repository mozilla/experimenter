import { render, act, screen } from "@testing-library/react";
import React from "react";

import { EXPERIMENT_DATA } from "experimenter-rapid/__tests__/visualizationTestData";
import SecondaryMetricTable from "experimenter-rapid/components/visualization/SecondaryMetricTable";

const PROBESET_D = "probeset_d";

describe("<SecondaryMetricTable />", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = ["Count", "Relative Improvement"];
    await act(async () => {
      render(
        <SecondaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_D}
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
        <SecondaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_D}
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
        <SecondaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_D}
        />,
      );
    });

    expect(screen.getAllByText("control")).toHaveLength(2);
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("shows the positive improvement bar", async () => {
    await act(async () => {
      render(
        <SecondaryMetricTable
          experimentData={EXPERIMENT_DATA}
          probeset={PROBESET_D}
        />,
      );
    });

    const negativeBlock = screen.queryByTestId("negative-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("positive-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("doesn't show data rows when no data is available", async () => {
    const newData = Object.assign(EXPERIMENT_DATA, { analysis: undefined });
    await act(async () => {
      render(
        <SecondaryMetricTable experimentData={newData} probeset={PROBESET_D} />,
      );
    });

    const rowForTreatmentResults = screen.queryByText("treatment");
    const rowForControlResults = screen.queryByText("control");
    expect(rowForTreatmentResults).not.toBeInTheDocument();
    expect(rowForControlResults).not.toBeInTheDocument();
  });
});
