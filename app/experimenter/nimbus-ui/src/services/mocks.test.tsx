/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { InMemoryCache } from "@apollo/client";
import { render, screen } from "@testing-library/react";
import { createCache, MockedCache } from "./mocks";

describe("services/mocks", () => {
  describe("createCache", () => {
    it("returns an instance of InMemoryCache", () => {
      expect(createCache()).toBeInstanceOf(InMemoryCache);
    });
  });

  describe("MockedCache", () => {
    it("renders children if there are any", () => {
      render(
        <MockedCache>
          <p>Oh No, My Stocks!</p>
        </MockedCache>,
      );

      expect(screen.queryByText("Oh No, My Stocks!")).toBeInTheDocument();
    });

    it("renders nothing if no children", () => {
      render(<MockedCache />);
      // 1 = an empty <div>
      expect(document.body.children).toHaveLength(1)
    });
  });
});
