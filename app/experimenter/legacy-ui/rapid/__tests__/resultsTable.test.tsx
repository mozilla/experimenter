import { render, act, screen } from "@testing-library/react";
import React from "react";

import { EXPERIMENT_DATA } from "experimenter-rapid/__tests__/visualizationTestData";
import ResultsTable from "experimenter-rapid/components/visualization/ResultsTable";

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
