/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  screen,
  waitFor,
  render,
  fireEvent,
  act,
} from "@testing-library/react";
import { Subject, MOCK_EXPERIMENT } from "./mocks";
import { AUDIENCE_DOC_URL } from ".";
import { MOCK_CONFIG } from "../../lib/mocks";

describe("FormAudience", () => {
  it("renders without error", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    expect(screen.getByTestId("learn-more-link")).toHaveAttribute(
      "href",
      AUDIENCE_DOC_URL,
    );
    const targetingConfigSlug = screen.queryByTestId("targetingConfigSlug");
    expect(targetingConfigSlug).toBeInTheDocument();
    expect((targetingConfigSlug as HTMLSelectElement).value).toEqual(
      MOCK_CONFIG!.targetingConfigSlug![0]!.value,
    );

    // Assert that we have all the channels for our application available
    for (const channel of MOCK_CONFIG.channel!.filter((channel) =>
      ["DESKTOP_NIGHTLY"].includes(channel?.value!),
    )) {
      const { label } = channel!;
      expect(screen.getByText(label!)).toBeInTheDocument();
    }

    // Assert that none of the channels that don't belong to our application are available
    for (const channel of MOCK_CONFIG.channel!.filter(
      (channel) =>
        !["DESKTOP_NIGHTLY", "DESKTOP_BETA"].includes(channel?.value!),
    )) {
      const { label } = channel!;
      expect(screen.queryByText(label!)).not.toBeInTheDocument();
    }
  });

  it("renders server errors", async () => {
    const submitErrors = {
      "*": ["Big bad server thing happened"],
      channel: ["Cannot tune in this channel"],
      firefoxMinVersion: ["Bad min version"],
      targetingConfigSlug: ["This slug is icky"],
      populationPercent: ["This is not a percentage"],
      totalEnrolledClients: ["Need a number here, bud."],
      proposedEnrollment: ["Emoji are not numbers"],
      proposedDuration: ["No negative numbers"],
    };
    const { container } = render(<Subject submitErrors={submitErrors} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    for (const [fieldName, [error]] of Object.entries(submitErrors)) {
      if (fieldName === "*") {
        expect(screen.getByTestId("submit-error")).toHaveTextContent(error);
      } else {
        expect(
          container.querySelector(`.invalid-feedback[data-for=${fieldName}`),
        ).toHaveTextContent(error);
      }
    }
  });

  it("renders without error with a partial experiment", async () => {
    render(
      <Subject
        config={{
          ...MOCK_CONFIG,
          targetingConfigSlug: [
            { __typename: "NimbusLabelValueType", label: null, value: null },
          ],
        }}
        experiment={{
          ...MOCK_EXPERIMENT,
          firefoxMinVersion: null,
          targetingConfigSlug: null,
          populationPercent: null,
          proposedEnrollment: null,
          proposedDuration: null,
        }}
      />,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const [fieldName, expected] of [
      ["populationPercent", "0"],
      ["proposedEnrollment", "7"],
      ["proposedDuration", "28"],
      ["firefoxMinVersion", ""],
      ["targetingConfigSlug", ""],
    ] as const) {
      const field = screen.queryByTestId(fieldName);
      expect(field).toBeInTheDocument();
      expect((field as HTMLInputElement).value).toEqual(expected);
    }
  });

  it("calls onNext when next button is clicked", async () => {
    const onNext = jest.fn();
    render(<Subject {...{ onNext }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("next-button"));
    expect(onNext).toHaveBeenCalled();
  });

  it("disables next button when experiment is not ready for review", async () => {
    const onNext = jest.fn();
    render(
      <Subject
        {...{
          onNext,
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              __typename: "NimbusReadyForReviewType",
              ready: false,
              message: "Test",
            },
          },
        }}
      />,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    const nextButton = screen.getByTestId("next-button");
    expect(nextButton).toBeDisabled();
    fireEvent.click(nextButton);
    expect(onNext).not.toHaveBeenCalled();
  });

  it("calls onSubmit when save button is clicked", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toHaveTextContent("Save");
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(onSubmit).toHaveBeenCalled();
    const [[submitData]] = onSubmit.mock.calls;
    expect(submitData).toEqual({
      channel: MOCK_EXPERIMENT.channel,
      firefoxMinVersion: MOCK_EXPERIMENT.firefoxMinVersion,
      targetingConfigSlug: MOCK_EXPERIMENT.targetingConfigSlug,
      populationPercent: "" + MOCK_EXPERIMENT.populationPercent,
      totalEnrolledClients: "" + MOCK_EXPERIMENT.totalEnrolledClients,
      proposedEnrollment: "" + MOCK_EXPERIMENT.proposedEnrollment,
      proposedDuration: "" + MOCK_EXPERIMENT.proposedDuration,
    });
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

  it("marks input fields as invalid when blank", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "channel",
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
      "firefoxMinVersion",
      "targetingConfigSlug",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
        fireEvent.change(field, { target: { value: "" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}`),
      ).toHaveTextContent("This field may not be blank.");
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
              __typename: "NimbusReadyForReviewType",
              ready: false,
              message: {
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
    expect(screen.queryByTestId("missing-enrollment")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-duration")).toBeInTheDocument();
  });
});
