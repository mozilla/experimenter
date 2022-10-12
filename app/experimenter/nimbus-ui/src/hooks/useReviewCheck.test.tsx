/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { render, screen, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import React from "react";
import { editPages } from "../components/AppLayoutWithSidebar";
import { SERVER_ERRORS } from "../lib/constants";
import { MockedCache, mockExperimentQuery } from "../lib/mocks";
import { useReviewCheck } from "./useReviewCheck";

describe("hooks/useReviewCheck", () => {
  const readyMessages = {
    publicDescription: [SERVER_ERRORS.NULL_FIELD],
    proposedDuration: [SERVER_ERRORS.NULL_FIELD],
    proposedEnrollment: [SERVER_ERRORS.NULL_FIELD],
    firefoxMinVersion: [SERVER_ERRORS.NULL_FIELD],
    targetingConfigSlug: [SERVER_ERRORS.NULL_FIELD],
    referenceBranch: [SERVER_ERRORS.NULL_FIELD],
    channel: [SERVER_ERRORS.NULL_FIELD],
    populationPercent: [
      "Ensure this value is greater than or equal to 0.0001.",
    ],
    riskBrand: [SERVER_ERRORS.NULL_FIELD],
    riskRevenue: [SERVER_ERRORS.NULL_FIELD],
    riskPartnerRelated: [SERVER_ERRORS.NULL_FIELD],
  };

  const pageNames = {
    publicDescription: "overview",
    proposedDuration: "audience",
    proposedEnrollment: "audience",
    firefoxMinVersion: "audience",
    targetingConfigSlug: "audience",
    referenceBranch: "branches",
    channel: "audience",
    populationPercent: "audience",
    riskBrand: "overview",
    riskRevenue: "overview",
    riskPartnerRelated: "overview",
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
        warnings: { referenceBranch: ["JSON is on fire"] },
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
          publicDescription: [SERVER_ERRORS.NULL_FIELD],
          referenceBranch: [SERVER_ERRORS.NULL_FIELD],
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
