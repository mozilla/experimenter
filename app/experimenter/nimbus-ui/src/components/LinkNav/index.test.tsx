/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  createHistory,
  createMemorySource,
  LocationProvider,
} from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
import LinkNav from ".";
import { BASE_PATH } from "../../lib/constants";

describe("LinkNav", () => {
  it("renders as expected when inactive", async () => {
    render(<Subject route="active-page" location="somewhere-else" />);
    const link = screen.getByTestId("LinkNav");
    expect(link).not.toHaveClass("text-primary");
    expect(link).toHaveClass("text-dark");
  });

  it("renders as expected when active", async () => {
    render(<Subject route="active-page" location="active-page" />);
    const link = screen.getByTestId("LinkNav");
    expect(link).toHaveClass("text-primary");
    expect(link).not.toHaveClass("text-dark");
  });
});

const Subject = ({ route, location }: { route: string; location: string }) => {
  const history = createHistory(createMemorySource(`${BASE_PATH}/${location}`));
  return (
    <LocationProvider history={history}>
      <LinkNav testid="LinkNav" route={route}>
        Hello
      </LinkNav>
    </LocationProvider>
  );
};
