/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { slugify } from "./slugify";

describe("slugify", () => {
  it("should follow Django's implementation in Python", () => {
    // Borrowed test cases from Django:
    // https://github.com/django/django/blob/main/tests/utils_tests/test_text.py#L192-L208
    const items = [
      ["Hello, World!", "hello-world"],
      ["spam & eggs", "spam-eggs"],
      [" multiple---dash and  space ", "multiple-dash-and-space"],
      ["\t whitespace-in-value \n", "whitespace-in-value"],
      ["underscore_in-value", "underscore_in-value"],
      ["__strip__underscore-value___", "strip__underscore-value"],
      ["--strip-dash-value---", "strip-dash-value"],
      ["__strip-mixed-value---", "strip-mixed-value"],
      ["_ -strip-mixed-value _-", "strip-mixed-value"],
      [undefined, ""],
      // No unicode tests, since we don't use allow_unicode=True anywhere
    ];
    for (const [value, expected] of items) {
      expect(slugify(value)).toEqual(expected);
    }
  });
});
