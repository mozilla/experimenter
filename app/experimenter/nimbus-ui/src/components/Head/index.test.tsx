/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { screen, waitFor } from "@testing-library/dom";
import { render } from "@testing-library/react";
import React from "react";
import Head from ".";

describe("Head", () => {
  fit("sets the page's <head> content", () => {
    render(
      <Head title="Lead, SD">
        <meta data-testid="meta-tag" name="lorem-ipsum" content="foo" />
      </Head>,
    );

    waitFor(() => {
      expect(document.title).toEqual("Lead, SD | Experimenter");
      expect(screen.queryByTestId("meta-tag")).toBeInTheDocument();
    });
  });
});
