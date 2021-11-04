/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { createMemorySource } from "@reach/router";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React, { useState } from "react";
import { RouterSlugProvider } from "../lib/test-utils";
import { useScrollToLocationHash } from "./useScrollToLocationHash";

describe("hooks/useScrollToLocationHash", () => {
  let mockGetElementById: any;
  let mockScrollIntoView: any;

  beforeAll(() => {
    mockScrollIntoView = jest.fn();
    mockGetElementById = jest
      .fn()
      .mockReturnValue({ scrollIntoView: mockScrollIntoView });
    Object.defineProperty(global.document, "getElementById", {
      value: mockGetElementById,
    });
  });

  it("does nothing without a hash in the location", async () => {
    render(<Subject />);
    fireEvent.click(screen.getByTestId("stop-loading"));
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
      expect(mockGetElementById).not.toHaveBeenCalled();
      expect(mockScrollIntoView).not.toHaveBeenCalled();
    });
  });

  it("scrolls to the hash after loading", async () => {
    render(<Subject hash="content" />);
    fireEvent.click(screen.getByTestId("stop-loading"));
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
      expect(mockGetElementById).toHaveBeenCalledWith("content");
      expect(mockScrollIntoView).toHaveBeenCalled();
    });
    fireEvent.click(screen.getByTestId("re-render"));
    await waitFor(() => {
      expect(mockGetElementById).toHaveBeenCalledTimes(1);
      expect(mockScrollIntoView).toHaveBeenCalledTimes(1);
    });
  });
});

const Subject = ({ hash }: { hash?: string }) => {
  const mockHistorySource = createMemorySource("/demo-slug/edit");
  if (hash) {
    // @ts-ignore too lazy to define the types for this, but it works in practice
    mockHistorySource.history.entries[0].hash = hash;
  }
  return (
    <RouterSlugProvider {...{ mockHistorySource }}>
      <SubjectInner />
    </RouterSlugProvider>
  );
};

const SubjectInner = () => {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  useScrollToLocationHash();
  return (
    <div>
      {loading ? (
        <div data-testid="loading">Loading...</div>
      ) : (
        <p data-testid="content" id="content">
          Hello world, count = {count}
        </p>
      )}
      <button data-testid="stop-loading" onClick={() => setLoading(false)}>
        Stop loading
      </button>
      <button
        data-testid="re-render"
        onClick={() => setCount((count) => count + 1)}
      >
        Re-render
      </button>
    </div>
  );
};
