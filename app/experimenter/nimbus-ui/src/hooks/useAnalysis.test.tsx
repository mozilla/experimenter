/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, renderHook } from "@testing-library/react-hooks";
import fetchMock from "jest-fetch-mock";
import { useAnalysis } from ".";

describe("hooks/useVisualization", () => {
  it("fetches from the visualization endpoint and returns data", async () => {
    fetchMock.enableMocks();

    const slug = "hungry";
    const data = { burrito: "Crunchwrap Supreme®" };
    fetchMock.mockResponseOnce(JSON.stringify(data));

    const { result } = renderHook(() => useAnalysis());
    await act(async () => void result.current.execute([slug]));

    expect(fetch).toHaveBeenCalledWith(`/api/v3/visualization/${slug}/`, {
      headers: { "Content-Type": "application/json" },
      method: "GET",
    });

    expect(result.current.result).toEqual(data);
    expect(result.current.loading).toBeFalsy();

    fetchMock.disableMocks();
  });
});
