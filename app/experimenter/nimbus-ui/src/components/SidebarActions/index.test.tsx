/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import { Subject } from "./mocks";

describe("SidebarActions", () => {
  it("renders sidebar actions content", () => {
    render(<Subject />);
    expect(screen.getByTestId("SidebarActions")).toBeInTheDocument();
  });

  it("renders a disabled archive button", () => {
    render(<Subject experiment={{ canArchive: false }} />);
    expect(screen.getByTestId("action-archive")).toHaveClass("text-muted");
  });

  it("renders an enabled archive button", () => {
    render(<Subject experiment={{ canArchive: true }} />);
    expect(screen.getByTestId("action-archive")).toHaveAttribute(
      "href",
      "/nimbus/my-special-slug/#",
    );
  });
});
