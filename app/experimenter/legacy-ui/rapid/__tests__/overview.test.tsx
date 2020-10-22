import { render, act, screen } from "@testing-library/react";
import React from "react";

import { EXPERIMENT_DATA } from "experimenter-rapid/__tests__/visualizationTestData";
import Overview from "experimenter-rapid/components/visualization/Overview";

describe("<Overview />", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = ["Targeting", "Probe Sets", "Owner"];

    await act(async () => {
      render(<Overview experimentData={EXPERIMENT_DATA} />);
    });

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has the expected targeting", async () => {
    await act(async () => {
      render(<Overview experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByText("Firefox 78.0+")).toBeInTheDocument();
    expect(screen.getByText("Firefox Release")).toBeInTheDocument();
    expect(screen.getByText("US users (en)")).toBeInTheDocument();
  });

  it("has the expected probe sets", async () => {
    await act(async () => {
      render(<Overview experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByText("Picture-in-Picture")).toBeInTheDocument();
  });

  it("has the experiment owner", async () => {
    await act(async () => {
      render(<Overview experimentData={EXPERIMENT_DATA} />);
    });

    expect(screen.getByText("test@owner.com")).toBeInTheDocument();
  });
});
