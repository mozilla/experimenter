/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { PRIMARY_OUTCOMES_TOOLTIP, SECONDARY_OUTCOMES_TOOLTIP } from ".";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import { Subject } from "./mocks";

describe("FormMetrics", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () =>
      expect(screen.getByTestId("FormMetrics")).toBeInTheDocument(),
    );

    expect(screen.getByTestId("tooltip-primary-outcomes")).toHaveAttribute(
      "data-tip",
      PRIMARY_OUTCOMES_TOOLTIP,
    );
    expect(screen.getByTestId("tooltip-secondary-outcomes")).toHaveAttribute(
      "data-tip",
      SECONDARY_OUTCOMES_TOOLTIP,
    );
  });

  it("calls onSave when save and next buttons are clicked", async () => {
    const onSave = jest.fn();
    render(<Subject {...{ onSave }} />);

    const submitButton = screen.getByTestId("submit-button");
    const nextButton = screen.getByTestId("next-button");
    await act(async () => {
      fireEvent.click(submitButton);
      fireEvent.click(nextButton);
    });
    expect(onSave).toHaveBeenCalledTimes(2);
  });

  it("disables save when loading", async () => {
    const onSave = jest.fn();
    render(<Subject {...{ onSave, isLoading: true }} />);

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent("Saving");

    await act(async () => {
      fireEvent.click(submitButton);
      fireEvent.submit(screen.getByTestId("FormMetrics"));
    });

    expect(onSave).not.toHaveBeenCalled();
  });

  it("displays saving button when loading", async () => {
    const { experiment } = mockExperimentQuery("boo");
    const onSave = jest.fn();
    render(<Subject {...{ onSave, experiment, isLoading: true }} />);

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toHaveTextContent("Saving");
  });

  it("displays saved primary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      primaryOutcomes: [MOCK_CONFIG.probeSets![0]],
    });

    render(<Subject {...{ experiment }} />);

    const primaryOutcomes = screen.getByTestId("primary-outcomes");
    expect(primaryOutcomes).toHaveTextContent("Probe Set A");
  });

  it("displays saved secondary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      secondaryOutcomes: [MOCK_CONFIG.probeSets![0]],
    });
    render(<Subject {...{ experiment }} />);

    const secondaryOutcomes = screen.getByTestId("secondary-outcomes");
    expect(secondaryOutcomes).toHaveTextContent("Probe Set A");
  });

  it("selects a primary outcome and excludes it from secondary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
    });

    render(<Subject {...{ experiment }} />);
    const primaryOutcomes = screen.getByTestId("primary-outcomes");
    const secondaryOutcomes = screen.getByTestId("secondary-outcomes");

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    await act(async () => {
      expect(primaryOutcomes).toHaveTextContent("Probe Set A");
      expect(primaryOutcomes).toHaveTextContent("Probe Set B");
      expect(primaryOutcomes).toHaveTextContent("Probe Set C");
    });

    fireEvent.click(screen.getByText("Probe Set A"));
    await act(async () => {
      expect(primaryOutcomes).toHaveTextContent("Probe Set A");
      expect(primaryOutcomes).not.toHaveTextContent("Probe Set B");
      expect(primaryOutcomes).not.toHaveTextContent("Probe Set C");
    });

    fireEvent.keyDown(secondaryOutcomes.children[1], { key: "ArrowDown" });
    await act(async () => {
      expect(secondaryOutcomes).not.toHaveTextContent("Probe Set A");
      expect(secondaryOutcomes).toHaveTextContent("Probe Set B");
      expect(secondaryOutcomes).toHaveTextContent("Probe Set C");
    });
  });

  it("selects a secondary outcome and excludes it from primary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
    });

    render(<Subject {...{ experiment }} />);

    const primaryOutcomes = screen.getByTestId("primary-outcomes");
    const secondaryOutcomes = screen.getByTestId("secondary-outcomes");

    fireEvent.keyDown(secondaryOutcomes.children[1], { key: "ArrowDown" });
    await act(async () => {
      expect(secondaryOutcomes).toHaveTextContent("Probe Set A");
      expect(secondaryOutcomes).toHaveTextContent("Probe Set B");
      expect(secondaryOutcomes).toHaveTextContent("Probe Set C");
    });

    fireEvent.click(screen.getByText("Probe Set A"));
    await act(async () => {
      expect(secondaryOutcomes).toHaveTextContent("Probe Set A");
      expect(secondaryOutcomes).not.toHaveTextContent("Probe Set B");
      expect(secondaryOutcomes).not.toHaveTextContent("Probe Set C");
    });

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    await act(async () => {
      expect(primaryOutcomes).not.toHaveTextContent("Probe Set A");
      expect(primaryOutcomes).toHaveTextContent("Probe Set B");
      expect(primaryOutcomes).toHaveTextContent("Probe Set C");
    });
  });

  it("allows maximum 2 primary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
    });

    render(<Subject {...{ experiment }} />);

    const primaryOutcomes = screen.getByTestId("primary-outcomes");

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText("Probe Set A"));

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText("Probe Set B"));

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText("Probe Set C"));
    fireEvent.keyDown(primaryOutcomes.children[1], { key: "Escape" });

    await act(async () => {
      expect(primaryOutcomes).toHaveTextContent("Probe Set A");
      expect(primaryOutcomes).toHaveTextContent("Probe Set B");
      expect(primaryOutcomes).not.toHaveTextContent("Probe Set C");
    });
  });
});
