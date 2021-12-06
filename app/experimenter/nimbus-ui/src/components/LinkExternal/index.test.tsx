/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import LinkExternal from "./index";

it("renders without imploding", () => {
  const className = "mozilla-link";
  const href = "https://mozilla.org/";
  const textContent = "Keep the internet open and accessible to all.";

  render(
    <LinkExternal {...{ className }} {...{ href }}>
      {textContent}
    </LinkExternal>,
  );

  const link = screen.getByTestId("link-external");

  expect(link).toBeInTheDocument();
  expect(link).toHaveClass(className);
  expect(link).toHaveProperty("href", href);
  expect(link).toHaveTextContent(textContent);
});
