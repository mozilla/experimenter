/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { act, render } from "@testing-library/react";
import { exitHandler, useExitWarning } from "./useExitWarning";

describe("hooks/useExitWarning", () => {
  describe("exitHandler", () => {
    it("correctly warns on exit", () => {
      const event = new Event("beforeunload");
      jest.spyOn(event, "preventDefault");
      exitHandler(event);
      expect(event.preventDefault).toHaveBeenCalled();
    });
  });

  describe("useExitWarning", () => {
    let shouldWarnFn: () => void;
    let addListener: jest.SpyInstance;
    let removeListener: jest.SpyInstance;

    const TestExitWarning = ({
      shouldWarn = false,
    }: {
      shouldWarn?: boolean;
    }) => {
      shouldWarnFn = useExitWarning(shouldWarn);
      return <p>Danbury, CT</p>;
    };

    beforeAll(() => {
      addListener = jest.spyOn(window, "addEventListener");
      removeListener = jest.spyOn(window, "removeEventListener");
    });

    afterEach(() => {
      addListener.mockReset();
      removeListener.mockReset();
    });

    afterAll(() => {
      addListener.mockRestore();
      removeListener.mockRestore();
    });

    it("doesn't warn by default when you leave the page", () => {
      render(<TestExitWarning />);
      expect(addListener).not.toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function),
      );
    });

    it("doesn't warn by default when you leave the page when an init value is not passed in", () => {
      const TestExitWarningDefaultInit = () => {
        shouldWarnFn = useExitWarning();
        return <p>Danbury, CT</p>;
      };

      render(<TestExitWarningDefaultInit />);
      expect(addListener).not.toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function),
      );
    });

    it("doesn't warn when you tell it not to when you leave the page", async () => {
      render(<TestExitWarning shouldWarn={true} />);
      expect(addListener).toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function),
      );

      await act(async () => shouldWarnFn(false));
      expect(removeListener).toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function),
      );
    });

    it("warns when you tell it to when you leave the page", async () => {
      render(<TestExitWarning shouldWarn={true} />);

      expect(addListener).toHaveBeenCalledWith(
        "beforeunload",
        expect.any(Function),
      );
    });
  });
});
