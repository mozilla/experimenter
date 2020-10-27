/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render } from "@testing-library/react";
import ExperimentNotFound from ".";
import { BASE_PATH } from "../../lib/constants";

describe("PageExperimentNotFound", () => {
  it("renders as expected", () => {
    render(<ExperimentNotFound slug="foo-bar-baz" />);
    expect(screen.getByTestId("not-found")).toHaveTextContent("foo-bar-baz");
    expect(screen.getByTestId("not-found-home")).toHaveAttribute(
      "href",
      BASE_PATH,
    );
  });
});
