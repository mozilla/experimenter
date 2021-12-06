/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, waitFor } from "@testing-library/react";
import React from "react";
import Head from ".";

describe("Head", () => {
  it("sets the page's <head> content", async () => {
    render(
      <Head title="Lead, SD">
        <meta data-testid="meta-tag" name="lorem-ipsum" content="foo" />
      </Head>,
    );

    await waitFor(() => {
      expect(document.title).toEqual("Lead, SD | Experimenter");
    });
  });
});
