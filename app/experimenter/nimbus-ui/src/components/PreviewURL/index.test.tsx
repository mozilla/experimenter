/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import selectEvent from "react-select-event";
import PreviewURL from ".";
import { mockExperimentQuery } from "../../lib/mocks";

const { experiment } = mockExperimentQuery("preview-url-slug");

describe("PreviewURL", () => {
  beforeAll(() => {
    // This doesn't exist in the virtual dom of jest
    Object.assign(navigator, {
      clipboard: {
        writeText: () => {},
      },
    });
  });
  it("renders as expected", () => {
    render(<PreviewURL {...experiment} />);

    screen.queryByText("Preview URL");
  });
  it("does not render when missing content", () => {
    render(<PreviewURL {...experiment} referenceBranch={null} />);

    expect(screen.queryByText("Preview URL")).toBeNull();
  });
  it("shows the correct preview URL", () => {
    render(<PreviewURL {...experiment} />);

    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=control",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=control&optin_collection=nimbus-preview",
      ),
    ).toBeInTheDocument();
  });
  it("should update the preview URL", async () => {
    const { getByLabelText } = render(<PreviewURL {...experiment} />);

    await selectEvent.select(getByLabelText("Selected Branch"), ["treatment"]);

    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=treatment",
      ),
    ).toBeInTheDocument();
  });
  it("should copy to clipboard", async () => {
    jest.spyOn(navigator.clipboard, "writeText");
    render(<PreviewURL {...experiment} />);
    const previewArea = await screen.findByText(
      "about:studies?optin_slug=preview-url-slug&optin_branch=control",
    );
    fireEvent.click(previewArea);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "about:studies?optin_slug=preview-url-slug&optin_branch=control",
    );
  });
});
