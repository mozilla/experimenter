/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import TableSignoff from "src/components/PageSummary/TableSignoff";

describe("TableSignoff", () => {
  it("handles signoff change events", async () => {
    const handleLegalSignoffChangeMock = jest.fn();
    const handleQaSignoffChangeMock = jest.fn();
    const handleVpSignoffChangeMock = jest.fn();

    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: false,
          vpSignoff: false,
          legalSignoff: false,
        }}
        legalSignoff={false}
        qaSignoff={false}
        vpSignoff={false}
        onLegalSignoffChange={handleLegalSignoffChangeMock}
        onQaSignoffChange={handleQaSignoffChangeMock}
        onVpSignoffChange={handleVpSignoffChangeMock}
      />,
    );

    await userEvent.click(screen.getByTestId("is-legalsignoff-checkbox"));
    expect(handleLegalSignoffChangeMock).toHaveBeenCalledWith(true);

    await userEvent.click(screen.getByTestId("is-qasignoff-checkbox"));
    expect(handleQaSignoffChangeMock).toHaveBeenCalledWith(true);

    await userEvent.click(screen.getByTestId("is-vpsignoff-checkbox"));
    expect(handleVpSignoffChangeMock).toHaveBeenCalledWith(true);
  });

  it("shows no recommended signoff", async () => {
    render(
      <TableSignoff
        signoffRecommendations={{
          qaSignoff: false,
          vpSignoff: false,
          legalSignoff: false,
        }}
        legalSignoff={false}
        qaSignoff={false}
        vpSignoff={false}
        onLegalSignoffChange={() => {}}
        onQaSignoffChange={() => {}}
        onVpSignoffChange={() => {}}
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
        legalSignoff={false}
        qaSignoff={false}
        vpSignoff={false}
        onLegalSignoffChange={() => {}}
        onQaSignoffChange={() => {}}
        onVpSignoffChange={() => {}}
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
        legalSignoff={false}
        qaSignoff={false}
        vpSignoff={false}
        onLegalSignoffChange={() => {}}
        onQaSignoffChange={() => {}}
        onVpSignoffChange={() => {}}
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
        legalSignoff={false}
        qaSignoff={false}
        vpSignoff={false}
        onLegalSignoffChange={() => {}}
        onQaSignoffChange={() => {}}
        onVpSignoffChange={() => {}}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("table-signoff-legal")).toHaveTextContent(
        "Recommended",
      ),
    );
  });
});
