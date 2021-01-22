/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, render } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { useAnalysis } from "./useAnalysis";

describe("hooks/useVisualization", () => {
  describe("useVisualization", () => {
    let hook: ReturnType<typeof useAnalysis>;

    const TestHook = () => {
      hook = useAnalysis();
      return <p>Algonquin Provincial Park</p>;
    };

    it("fetches from the visualization endpoint and returns data", async () => {
      fetchMock.enableMocks();

      const slug = "hungry";
      const data = { burrito: "Crunchwrap Supreme®" };
      fetchMock.mockResponseOnce(JSON.stringify(data));

      render(<TestHook />);

      await act(async () => void hook.execute([slug]));

      expect(fetch).toHaveBeenCalledWith(`/api/v3/visualization/${slug}/`, {
        headers: { "Content-Type": "application/json" },
        method: "GET",
      });

      expect(hook.result).toEqual(data);
      expect(hook.loading).toBeFalsy();

      fetchMock.disableMocks();
    });
  });
});
