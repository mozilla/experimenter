/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { optionalBoolString, optionalStringBool, pluralize } from "./utils";

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

describe("optionalStringBool", () => {
  it("returns null if an empty string is provided", () => {
    expect(optionalStringBool("")).toBeNull();
  });

  it("returns true if string is 'true'", () => {
    expect(optionalStringBool("true")).toBeTruthy();
  });

  it("returns false if string is not 'true'", () => {
    expect(optionalStringBool("false")).toBeFalsy();
  });
});

describe("optionalBoolString", () => {
  it("returns 'true' if true is provided", () => {
    expect(optionalBoolString(true)).toEqual("true");
  });

  it("returns 'false' if true is provided", () => {
    expect(optionalBoolString(false)).toEqual("false");
  });

  it("returns null if null or undefined is provided", () => {
    expect(optionalBoolString(null)).toBeNull();
    expect(optionalBoolString(undefined)).toBeNull();
  });
});
