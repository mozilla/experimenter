/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { useConfig } from "./useConfig";
import { MockedCache, MOCK_CONFIG } from "../lib/mocks";
import { render, waitFor } from "@testing-library/react";
import serverConfig from "../services/config";

describe("hooks/useConfig", () => {
  describe("useConfig", () => {
    let hook: ReturnType<typeof useConfig>;
    const config = { ...MOCK_CONFIG, ...serverConfig };

    const TestConfig = () => {
      hook = useConfig();
      return <p>Bière forte</p>;
    };

    it("returns the config", async () => {
      render(
        <MockedCache>
          <TestConfig />
        </MockedCache>,
      );

      await waitFor(() => expect(hook).toEqual(config));
    });
  });
});
