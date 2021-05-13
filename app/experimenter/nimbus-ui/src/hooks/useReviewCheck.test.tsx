/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { render, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import React from "react";
import { editPages } from "../components/AppLayoutWithSidebar";
import { MockedCache, mockExperimentQuery } from "../lib/mocks";
import { useReviewCheck } from "./useReviewCheck";

describe("hooks/useReviewCheck", () => {
  const readyMessages = {
    public_description: ["This field may not be null."],
    proposed_duration: ["This field may not be null."],
    proposed_enrollment: ["This field may not be null."],
    firefox_min_version: ["This field may not be null."],
    targeting_config_slug: ["This field may not be null."],
    reference_branch: ["This field may not be null."],
    channel: ["This field may not be null."],
    population_percent: [
      "Ensure this value is greater than or equal to 0.0001.",
    ],
    risk_brand: ["This field may not be null."],
    risk_revenue: ["This field may not be null."],
    risk_partner_related: ["This field may not be null."],
  };

  const pageNames = {
    public_description: "overview",
    proposed_duration: "audience",
    proposed_enrollment: "audience",
    firefox_min_version: "audience",
    targeting_config_slug: "audience",
    reference_branch: "branches",
    channel: "audience",
    population_percent: "audience",
    risk_brand: "overview",
    risk_revenue: "overview",
    risk_partner_related: "overview",
  };

  beforeAll(() => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });
  });

  const missingDetailsTest = (
    fieldName: keyof typeof readyMessages,
  ) => async () => {
    const readyMessage = {
      [fieldName]: readyMessages[fieldName],
    };
    const pageName = pageNames[fieldName];
    const { mock, experiment } = mockExperimentQuery("howdy", {
      readyForReview: {
        ready: false,
        message: readyMessage,
      },
    });
    const { result } = renderHook(() => useReviewCheck(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    await waitFor(() => {
      const { ready, invalidPages } = result.current;
      expect(ready).toBeFalsy();
      expect(invalidPages).toEqual(expect.arrayContaining([pageName]));
    });
  };

  let fieldName: keyof typeof readyMessages;
  for (fieldName in readyMessages) {
    it(
      `returns correct review info when missing details for ${fieldName}`,
      missingDetailsTest(fieldName),
    );
  }

  it("returns correct review info when not missing any details", async () => {
    const { mock, experiment } = mockExperimentQuery("howdy", {
      readyForReview: {
        ready: true,
        message: {},
      },
    });

    const { result } = renderHook(() => useReviewCheck(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    await waitFor(() => {
      const { ready, invalidPages } = result.current;
      expect(ready).toBeTruthy();
      expect(invalidPages).toEqual([]);
    });
  });

  it("returns a component that can render invalid pages", async () => {
    const { mock, experiment } = mockExperimentQuery("howdy", {
      readyForReview: {
        ready: false,
        message: {
          public_description: ["This field may not be null."],
          reference_branch: ["This field may not be null."],
          channel: ["This list may not be empty."],
        },
      },
    });

    const { result } = renderHook(() => useReviewCheck(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    const { InvalidPagesList } = result.current;
    const { getByText } = render(<InvalidPagesList />);

    editPages.forEach((page) => {
      // Currently metrics does not produce any
      // review-readiness messages
      if (page.slug === "metrics") {
        return;
      }

      getByText(page.name);
    });
  });
});

const wrapper = ({
  mocks = [],
  children,
}: {
  mocks?: MockedResponse[];
  children?: React.ReactNode;
}) => (
  <MockedCache {...{ mocks }}>{children as React.ReactElement}</MockedCache>
);
