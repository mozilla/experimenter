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
import { snakeToCamelCase } from "../../../lib/caseConversions";
import { EXTERNAL_URLS, FIELD_MESSAGES } from "../../../lib/constants";
import { MOCK_CONFIG } from "../../../lib/mocks";
import {
  NimbusExperimentChannel,
  NimbusExperimentFirefoxMinVersion,
  NimbusExperimentTargetingConfigSlug,
} from "../../../types/globalTypes";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

describe("FormAudience", () => {
  it("renders without error", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    expect(screen.getByTestId("learn-more-link")).toHaveAttribute(
      "href",
      EXTERNAL_URLS.WORKFLOW_MANA_DOC,
    );
    const targetingConfigSlug = screen.queryByTestId("targetingConfigSlug");
    expect(targetingConfigSlug).toBeInTheDocument();
    expect((targetingConfigSlug as HTMLSelectElement).value).toEqual(
      MOCK_CONFIG!.targetingConfigSlug![0]!.value,
    );

    // Assert that we have all the channels available
    for (const channel of MOCK_CONFIG.channel!) {
      const { label } = channel!;
      expect(screen.getByText(label!)).toBeInTheDocument();
    }
  });

  it("renders server errors", async () => {
    const submitErrors = {
      "*": ["Big bad server thing happened"],
      channel: ["Cannot tune in this channel"],
      firefox_min_version: ["Bad min version"],
      targeting_config_slug: ["This slug is icky"],
      population_percent: ["This is not a percentage"],
      total_enrolled_clients: ["Need a number here, bud."],
      proposed_enrollment: ["Emoji are not numbers"],
      proposed_duration: ["No negative numbers"],
    };
    const { container } = render(<Subject submitErrors={submitErrors} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    for (const [submitErrorName, [error]] of Object.entries(submitErrors)) {
      const fieldName = snakeToCamelCase(submitErrorName);
      if (fieldName === "*") {
        expect(screen.getByTestId("submit-error")).toHaveTextContent(error);
      } else {
        expect(
          container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
        ).toHaveTextContent(error);
      }
    }
  });

  it("renders without error with default values", async () => {
    renderSubjectWithDefaultValues();
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const [fieldName, expected] of [
      ["firefoxMinVersion", NimbusExperimentFirefoxMinVersion.NO_VERSION],
      ["populationPercent", "0.0"],
      ["proposedDuration", "0"],
      ["proposedEnrollment", "0"],
      ["targetingConfigSlug", NimbusExperimentTargetingConfigSlug.NO_TARGETING],
    ] as const) {
      const field = screen.queryByTestId(fieldName);
      expect(field).toBeInTheDocument();
      expect((field as HTMLInputElement).value).toEqual(expected);
    }
  });

  it("disables next button when experiment is not ready for review", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        {...{
          onSubmit,
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              ready: false,
              message: "Test",
            },
          },
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    const nextButton = screen.getByTestId("next-button");
    expect(nextButton).toBeDisabled();
    fireEvent.click(nextButton);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onSubmit when save and next buttons are clicked", async () => {
    const onSubmit = jest.fn();
    const expected = {
      channel: MOCK_EXPERIMENT.channel,
      firefoxMinVersion: MOCK_EXPERIMENT.firefoxMinVersion,
      targetingConfigSlug: MOCK_EXPERIMENT.targetingConfigSlug,
      populationPercent: "" + MOCK_EXPERIMENT.populationPercent,
      totalEnrolledClients: MOCK_EXPERIMENT.totalEnrolledClients,
      proposedEnrollment: "" + MOCK_EXPERIMENT.proposedEnrollment,
      proposedDuration: "" + MOCK_EXPERIMENT.proposedDuration,
    };
    render(<Subject {...{ onSubmit }} />);
    await screen.findByTestId("FormAudience");
    const submitButton = screen.getByTestId("submit-button");
    const nextButton = screen.getByTestId("next-button");

    await act(async () => {
      fireEvent.click(submitButton);
      fireEvent.click(nextButton);
    });
    expect(onSubmit).toHaveBeenCalledTimes(2);
    expect(onSubmit.mock.calls).toEqual([
      // Save button just saves
      [expected, false],
      // Next button advances to next page
      [expected, true],
    ]);
  });

  it("accepts commas in the expected number of clients field (EXP-761)", async () => {
    const enteredValue = "123,456,789";
    const expectedValue = 123456789;

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = screen.getByTestId("totalEnrolledClients");
      fireEvent.click(field);
      fireEvent.change(field, { target: { value: enteredValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].totalEnrolledClients).toEqual(
      expectedValue,
    );
  });

  it("requires positive numbers in numeric fields (EXP-956)", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
        fireEvent.change(field, { target: { value: "-123" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
  });

  it("does not require a selection for channel, ff min version, targeting config (EXP-957)", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);
    await screen.findByTestId("FormAudience");

    for (const label of ["Channel", "Min Version", "Advanced Targeting"]) {
      const field = screen.getByLabelText(label);
      fireEvent.change(field, { target: { value: "" } });
    }

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    const expectedValues = expect.objectContaining({
      channel: "NO_CHANNEL",
      firefoxMinVersion: "NO_VERSION",
      targetingConfigSlug: "NO_TARGETING",
    });
    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(expectedValues, false),
    );
  });

  it("does not have any required modified fields", async () => {
    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit-button"));
    });
    expect(onSubmit).toHaveBeenCalled();
  });

  it("does not call onSubmit when submitted while loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    const form = screen.getByTestId("FormAudience");
    await act(async () => {
      fireEvent.submit(form);
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("displays expected message on number-based inputs when invalid", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
        fireEvent.change(field, { target: { value: "hi" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
  });

  it("displays warning icons when server complains fields are missing", async () => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });

    const isMissingField = jest.fn(() => true);
    render(
      <Subject
        {...{
          isMissingField,
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              ready: false,
              message: {
                population_percent: ["This field may not be null."],
                proposed_duration: ["This field may not be null."],
                proposed_enrollment: ["This field may not be null."],
                firefox_min_version: ["This field may not be null."],
                targeting_config_slug: ["This field may not be null."],
                channel: ["This list may not be empty."],
              },
            },
          },
        }}
      />,
    );

    expect(isMissingField).toHaveBeenCalled();
    expect(screen.queryByTestId("missing-channel")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-ff-min")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-config")).toBeInTheDocument();
    expect(
      screen.queryByTestId("missing-population-percent"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("missing-clients")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-enrollment")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-duration")).toBeInTheDocument();
  });
});

const renderSubjectWithDefaultValues = (onSubmit = () => {}) =>
  render(
    <Subject
      {...{ onSubmit }}
      config={{
        ...MOCK_CONFIG,
        targetingConfigSlug: [
          {
            label: NimbusExperimentTargetingConfigSlug.NO_TARGETING,
            value: NimbusExperimentTargetingConfigSlug.NO_TARGETING,
          },
        ],
        firefoxMinVersion: [
          {
            label: NimbusExperimentFirefoxMinVersion.NO_VERSION,
            value: NimbusExperimentFirefoxMinVersion.NO_VERSION,
          },
        ],
        channel: [
          {
            label: NimbusExperimentChannel.NO_CHANNEL,
            value: NimbusExperimentChannel.NO_CHANNEL,
          },
        ],
      }}
      experiment={{
        ...MOCK_EXPERIMENT,
        firefoxMinVersion: NimbusExperimentFirefoxMinVersion.NO_VERSION,
        channel: NimbusExperimentChannel.NO_CHANNEL,
        populationPercent: "0.0",
        proposedDuration: 0,
        proposedEnrollment: 0,
        targetingConfigSlug: NimbusExperimentTargetingConfigSlug.NO_TARGETING,
      }}
    />,
  );
