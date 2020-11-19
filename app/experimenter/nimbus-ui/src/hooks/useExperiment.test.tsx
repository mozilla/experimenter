/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, waitFor } from "@testing-library/react";
import { useExperiment } from "./useExperiment";
import { MockedCache, mockExperimentQuery } from "../lib/mocks";

describe("hooks/useExperiment", () => {
  describe("useExperiment", () => {
    let hook: ReturnType<typeof useExperiment>;

    const TestExperiment = ({ slug }: { slug: string }) => {
      hook = useExperiment(slug);
      return <p>Notre-Dame-du-Bon-Conseil, QC</p>;
    };

    it("returns the experiment", async () => {
      const { mock, data } = mockExperimentQuery("howdy");

      render(
        <MockedCache mocks={[mock]}>
          <TestExperiment slug="howdy" />
        </MockedCache>,
      );

      await waitFor(() => expect(hook.experiment).toEqual(data));
    });

    it("returns notFound if no experiment found", async () => {
      const { mock } = mockExperimentQuery("howdy", null);

      render(
        <MockedCache mocks={[mock]}>
          <TestExperiment slug="howdy" />
        </MockedCache>,
      );

      await waitFor(() => expect(hook.notFound).toBeTruthy());
    });

    describe("ready for review", () => {
      const readyMessage = {
        public_description: ["This field may not be null."],
        proposed_duration: ["This field may not be null."],
        proposed_enrollment: ["This field may not be null."],
        firefox_min_version: ["This field may not be null."],
        targeting_config_slug: ["This field may not be null."],
        reference_branch: ["This field may not be null."],
        channels: ["This list may not be empty."],
      };

      it("returns correct review info when missing details", async () => {
        Object.defineProperty(window, "location", {
          value: {
            search: "?show-errors",
          },
        });

        const { mock } = mockExperimentQuery("howdy", {
          readyForReview: {
            __typename: "NimbusReadyForReviewType",
            ready: false,
            message: readyMessage,
          },
        });

        render(
          <MockedCache mocks={[mock]}>
            <TestExperiment slug="howdy" />
          </MockedCache>,
        );

        await waitFor(() => {
          const {
            ready,
            invalidPages,
            missingFields,
            isMissingField,
          } = hook.review;

          expect(ready).toBeFalsy();
          expect(invalidPages).toEqual(
            expect.arrayContaining(["overview", "branches", "audience"]),
          );
          expect(missingFields).toEqual(
            expect.arrayContaining(Object.keys(readyMessage)),
          );
          Object.keys(readyMessage).forEach((fieldName) => {
            expect(isMissingField(fieldName)).toBeTruthy();
          });
        });
      });

      it("returns correct review info when not missing any details", async () => {
        const { mock } = mockExperimentQuery("howdy", {
          readyForReview: {
            __typename: "NimbusReadyForReviewType",
            ready: true,
            message: {},
          },
        });

        render(
          <MockedCache mocks={[mock]}>
            <TestExperiment slug="howdy" />
          </MockedCache>,
        );

        await waitFor(() => {
          const {
            ready,
            invalidPages,
            missingFields,
            isMissingField,
          } = hook.review;

          expect(ready).toBeTruthy();
          expect(invalidPages).toEqual([]);
          expect(missingFields).toEqual([]);
          Object.keys(readyMessage).forEach((fieldName) => {
            expect(isMissingField(fieldName)).toBeFalsy();
          });
        });
      });
    });

    it("starts by loading", async () => {
      render(
        <MockedCache mocks={[]}>
          <TestExperiment slug="howdy" />
        </MockedCache>,
      );

      expect(hook.loading).toBeTruthy();
    });
  });
});
