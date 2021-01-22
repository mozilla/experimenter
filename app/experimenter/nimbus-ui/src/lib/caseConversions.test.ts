/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { camelToSnakeCase, snakeToCamelCase } from "./caseConversions";

describe("snakeToCamelCase", () => {
  it("converts snake_case to camelCase", () => {
    expect(snakeToCamelCase("this_is_a_test")).toEqual("thisIsATest");
  });
});

describe("camelToSnakeCase", () => {
  it("converts camelCase to snake_case", () => {
    expect(camelToSnakeCase("thisIsATest")).toEqual("this_is_a_test");
  });
});
