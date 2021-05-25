/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import { PRIMARY_OUTCOMES_TOOLTIP, SECONDARY_OUTCOMES_TOOLTIP } from ".";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import { assertSerializerMessages } from "../../../lib/test-utils";
import { Subject } from "./mocks";

const outcomeNames = MOCK_CONFIG.outcomes!.map(
  (outcome) => outcome!.friendlyName,
) as string[];

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
    const { experiment } = mockExperimentQuery("boo");

    render(<Subject {...{ experiment }} />);

    const primaryOutcomes = screen.getByTestId("primary-outcomes");
    expect(primaryOutcomes).toHaveTextContent(
      MOCK_CONFIG.outcomes![0]!.friendlyName!,
    );
  });

  it("displays saved secondary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo");
    render(<Subject {...{ experiment }} />);

    const secondaryOutcomes = screen.getByTestId("secondary-outcomes");
    expect(secondaryOutcomes).toHaveTextContent(
      MOCK_CONFIG.outcomes![1]!.friendlyName!,
    );
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
    await waitFor(async () => {
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[0]);
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[1]);
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[2]);
    });

    fireEvent.click(screen.getByText(outcomeNames[0]));
    await waitFor(async () => {
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[0]);
      expect(primaryOutcomes).not.toHaveTextContent(outcomeNames[1]);
      expect(primaryOutcomes).not.toHaveTextContent(outcomeNames[2]);
    });

    fireEvent.keyDown(secondaryOutcomes.children[1], { key: "ArrowDown" });
    await waitFor(async () => {
      expect(secondaryOutcomes).not.toHaveTextContent(outcomeNames[0]);
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[1]);
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[2]);
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
    await waitFor(async () => {
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[0]);
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[1]);
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[2]);
    });

    fireEvent.click(screen.getByText(outcomeNames[0]));
    await waitFor(async () => {
      expect(secondaryOutcomes).toHaveTextContent(outcomeNames[0]);
      expect(secondaryOutcomes).not.toHaveTextContent(outcomeNames[1]);
      expect(secondaryOutcomes).not.toHaveTextContent(outcomeNames[2]);
    });

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    await waitFor(async () => {
      expect(primaryOutcomes).not.toHaveTextContent(outcomeNames[0]);
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[1]);
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[2]);
    });
  });

  it("allows maximum primary outcomes", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
    });

    render(<Subject {...{ experiment }} />);

    const primaryOutcomes = screen.getByTestId("primary-outcomes");

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText(outcomeNames[0]));

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText(outcomeNames[1]));

    fireEvent.keyDown(primaryOutcomes.children[1], { key: "ArrowDown" });
    fireEvent.click(screen.getByText(outcomeNames[2]));
    fireEvent.keyDown(primaryOutcomes.children[1], { key: "Escape" });

    await waitFor(async () => {
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[0]);
      expect(primaryOutcomes).toHaveTextContent(outcomeNames[1]);
      expect(primaryOutcomes).not.toHaveTextContent(outcomeNames[2]);
    });
  });

  it("can display server review-readiness messages on all fields", async () => {
    await assertSerializerMessages(Subject, {
      primary_outcomes: ["Primarily, tell me what's up."],
      secondary_outcomes: ["On second thought..."],
    });
  });
});
