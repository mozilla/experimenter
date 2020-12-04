/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { Subject, MOCK_EXPERIMENT } from "./mocks";
import { MOCK_CONFIG } from "../../lib/mocks";

describe("FormAudience", () => {
  it("renders without error", () => {
    render(<Subject />);
  });

  it("renders without error with a partial experiment", () => {
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
                channels: ["This list may not be empty."],
              },
            },
          },
        }}
      />,
    );

    expect(isMissingField).toHaveBeenCalled();
    expect(screen.queryByTestId("missing-channels")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-ff-min")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-config")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-enrollment")).toBeInTheDocument();
    expect(screen.queryByTestId("missing-duration")).toBeInTheDocument();
  });
});
