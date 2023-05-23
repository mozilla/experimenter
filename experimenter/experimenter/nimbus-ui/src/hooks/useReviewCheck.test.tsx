/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { render, screen, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import React from "react";
import { editPages } from "src/components/AppLayoutWithSidebar";
import { useReviewCheck } from "src/hooks/useReviewCheck";
import { SERVER_ERRORS } from "src/lib/constants";
import { MockedCache, mockExperimentQuery } from "src/lib/mocks";

describe("hooks/useReviewCheck", () => {
  const readyMessages = {
    public_description: [SERVER_ERRORS.NULL_FIELD],
    proposed_duration: [SERVER_ERRORS.NULL_FIELD],
    proposed_enrollment: [SERVER_ERRORS.NULL_FIELD],
    firefox_min_version: [SERVER_ERRORS.NULL_FIELD],
    targeting_config_slug: [SERVER_ERRORS.NULL_FIELD],
    reference_branch: [SERVER_ERRORS.NULL_FIELD],
    channel: [SERVER_ERRORS.NULL_FIELD],
    population_percent: [
      "Ensure this value is greater than or equal to 0.0001.",
    ],
    risk_brand: [SERVER_ERRORS.NULL_FIELD],
    risk_revenue: [SERVER_ERRORS.NULL_FIELD],
    risk_partner_related: [SERVER_ERRORS.NULL_FIELD],
    localizations: [SERVER_ERRORS.NULL_FIELD],
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
    localizations: "branches",
  };

  beforeAll(() => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });
  });

  const missingDetailsTest =
    (fieldName: keyof typeof readyMessages) => async () => {
      const readyMessage = {
        [fieldName]: readyMessages[fieldName],
      };
      const pageName = pageNames[fieldName];
      const { mock, experiment } = mockExperimentQuery("howdy", {
        readyForReview: {
          ready: false,
          message: readyMessage,
          warnings: {},
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
        warnings: { reference_branch: ["JSON is on fire"] },
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
          public_description: [SERVER_ERRORS.NULL_FIELD],
          reference_branch: [SERVER_ERRORS.NULL_FIELD],
          channel: [SERVER_ERRORS.EMPTY_LIST],
        },
        warnings: {},
      },
    });

    const { result } = renderHook(() => useReviewCheck(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    const { InvalidPagesList } = result.current;
    render(<InvalidPagesList />);

    editPages.forEach((page) => {
      // Currently metrics does not produce any
      // review-readiness messages
      if (page.slug === "metrics") {
        return;
      }

      screen.getByText(page.name);
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
