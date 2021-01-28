/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { MockedCache, MOCK_CONFIG } from "../lib/mocks";
import serverConfig from "../services/config";
import { MockConfigContext, useConfig } from "./useConfig";

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

    it("supports config supplied via MockConfigContext", () => {
      const mockConfigValue = {
        version: "8675309",
      };
      const TestMockConfig = () => {
        const config = useConfig();
        return <p data-testid="config-value">{config.version}</p>;
      };
      render(
        <MockedCache>
          <MockConfigContext.Provider value={mockConfigValue}>
            <TestMockConfig />
          </MockConfigContext.Provider>
        </MockedCache>,
      );
      expect(screen.getByTestId("config-value")).toHaveTextContent(
        mockConfigValue.version,
      );
    });
  });
});
