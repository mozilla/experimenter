import { render, act, screen } from "@testing-library/react";
import React from "react";

import { EXPERIMENT_DATA } from "experimenter-rapid/__tests__/visualizationTestData";
import HighlightsTable from "experimenter-rapid/components/visualization/HighlightsTable";

describe("<HighlightsTable />", () => {
  it("has participants for all users shown for each variant", async () => {
    const EXPECTED_LABELS = ["participants", "All Users"];

    await act(async () => {
      render(<HighlightsTable experimentData={EXPERIMENT_DATA} />);
    });

    EXPECTED_LABELS.forEach((label) => {
      expect(
        screen.getAllByText(label, {
          exact: false,
        }),
      ).toHaveLength(2);
    });
  });

  it("has correctly labelled result significance", async () => {
    await act(async () => {
      render(<HighlightsTable experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.getByTestId("neutral-significance")).toBeInTheDocument();
  });

  it("has the expected control and treatment labels", async () => {
    await act(async () => {
      render(<HighlightsTable experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("doesn't show data rows when no data is available", async () => {
    const newData = Object.assign(EXPERIMENT_DATA, { analysis: undefined });
    await act(async () => {
      render(<HighlightsTable experimentData={newData} />);
    });

    const rowForTreatmentResults = screen.queryByText("treatment");
    const rowForControlResults = screen.queryByText("control");
    expect(rowForTreatmentResults).not.toBeInTheDocument();
    expect(rowForControlResults).not.toBeInTheDocument();
  });
});
