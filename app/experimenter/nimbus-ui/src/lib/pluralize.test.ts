/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import pluralize from "./pluralize";

describe("pluralize", () => {
  it("correctly return 0-count item", () => {
    expect(pluralize(0, "day")).toEqual("0 days");
  });

  it("correctly returns 1-count item", () => {
    expect(pluralize(1, "lamp")).toEqual("1 lamp");
  });

  it("correctly returns 2-count item", () => {
    expect(pluralize(2, "car")).toEqual("2 cars");
  });

  it("correctly returns item with alternative pluralization", () => {
    expect(pluralize(1, "factory", "factories")).toEqual("1 factory");
    expect(pluralize(10, "factory", "factories")).toEqual("10 factories");
  });
});
