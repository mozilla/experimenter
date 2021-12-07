/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render } from "@testing-library/react";
import React from "react";
import RichText from ".";

it("renders text with newlines converted to <br> tags", () => {
  const text = `Aliens

  Galactic Federation

  We are not ready`;

  const view = render(<RichText {...{ text }} />);

  // Each return should be replaced with a <br />
  const lineBreaks = view.container.querySelectorAll("br");
  expect(lineBreaks).toHaveLength(4);
});

it("renders text with strings that look like links converted to <a> tags", () => {
  const url1 = "https://www.mozilla.org/about/manifesto";
  const url2 = "http://foundation.mozilla.org/";
  const url3 = "www.mozilla.org/contribute";
  const url4 = "mozilla.org/about/leadership/";
  const text = `Mozilla Manifesto: ${url1}
  Mozilla Foundation: ${url2}
  Get Involved: ${url3}
  Leadership: ${url4}`;

  const view = render(<RichText {...{ text }} />);

  const anchors = view.container.querySelectorAll("a");
  expect(anchors).toHaveLength(3);

  expect(anchors[0]).toHaveProperty("href", url1);
  expect(anchors[0]).toHaveTextContent(url1);

  expect(anchors[1]).toHaveProperty("href", url2);
  expect(anchors[1]).toHaveTextContent(url2);

  // Non protocol links should be converted, with the text
  // unchanged but the href prepended with https://
  expect(anchors[2]).toHaveProperty("href", `https://${url3}`);
  expect(anchors[2]).toHaveTextContent(url3);
});
