/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import ExternalConfigAlert from ".";
import { MOCK_METADATA_EXTERNAL_CONFIG } from "../../../lib/visualization/mocks";

describe("ExternalConfigAlert", () => {
  it("renders all overrides as expected", () => {
    render(
      <ExternalConfigAlert
        externalConfig={{
          ...MOCK_METADATA_EXTERNAL_CONFIG,
        }}
      />,
    );

    expect(screen.getByTestId("external-config-start-date")).toHaveTextContent(
      "May 26",
    );
    expect(screen.getByTestId("external-config-end-date")).toHaveTextContent(
      "Jun 6",
    );
    expect(
      screen.getByTestId("external-config-enrollment-period"),
    ).toHaveTextContent("9 days");

    expect(
      screen.getByTestId("external-config-reference-branch"),
    ).toHaveTextContent("treatment");

    expect(screen.getByTestId("external-config-url")).toHaveProperty(
      "href",
      "https://github.com/mozilla/jetstream-config/",
    );
  });
});
