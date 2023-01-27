/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import ExperimentNotFound from "src/components/PageExperimentNotFound";
import { BASE_PATH } from "src/lib/constants";

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
