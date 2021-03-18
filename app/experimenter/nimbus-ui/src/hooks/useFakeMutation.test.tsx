/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, renderHook } from "@testing-library/react-hooks";
import { useFakeMutation } from "./useFakeMutation";

describe("hooks/useMockMutation", () => {
  it("simulates loading with a delay", async () => {
    const { result } = renderHook(() => useFakeMutation(1000));
    expect(result.current[1].loading).toEqual(false);
    let pending: Promise<void>;
    act(() => {
      pending = result.current[0]();
    });
    expect(result.current[1].loading).toEqual(true);
    await act(async () => {
      await pending!;
    });
    expect(result.current[1].loading).toEqual(false);
  });
});
