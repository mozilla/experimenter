/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import TableSignoff from ".";

describe("TableSignoff", () => {
  it("shows no recommended signoff", async () => {
    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: false,
          vpSignoff: false,
          legalSignoff: false,
        }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff")).not.toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows qa recommended signoff", async () => {
    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: true,
          vpSignoff: false,
          legalSignoff: false,
        }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-qa")).toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows vp recommended signoff", async () => {
    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: false,
          vpSignoff: true,
          legalSignoff: false,
        }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-vp")).toHaveTextContent(
        "Recommended",
      ),
    );
  });

  it("shows legal recommended signoff", async () => {
    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: false,
          vpSignoff: false,
          legalSignoff: true,
        }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-legal")).toHaveTextContent(
        "Recommended",
      ),
    );
  });
});
