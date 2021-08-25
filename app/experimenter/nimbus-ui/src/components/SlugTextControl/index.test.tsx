/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import SlugTextControl from ".";

describe("SlugTextControl", () => {
  it("renders as expected with defaultValue", () => {
    render(<SlugTextControl value={undefined} defaultValue={"Hello world"} />);
    expect(
      (screen.getByTestId("SlugTextControl") as HTMLInputElement).value,
    ).toEqual("hello-world");
  });
  it("renders as expected with value", () => {
    render(
      <SlugTextControl value={"Goodbye world"} defaultValue={"Hello world"} />,
    );
    expect(
      (screen.getByTestId("SlugTextControl") as HTMLInputElement).value,
    ).toEqual("goodbye-world");
  });
});
