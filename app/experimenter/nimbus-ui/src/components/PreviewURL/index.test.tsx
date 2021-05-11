/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import selectEvent from "react-select-event";
import PreviewURL from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { experiment } = mockExperimentQuery("preview-url-slug");

describe("PreviewURL", () => {
  beforeAll(() => {
    // This doesn't exist in the virtual dom of jest
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(),
      },
    });
  });
  it("renders as expected LIVE", () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />,
    );

    expect(screen.queryByText("Preview URL")).toBeInTheDocument();
  });
  it("renders as expected PREVIEW", () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.PREVIEW })}
      />,
    );

    expect(screen.queryByText("Preview URL")).toBeInTheDocument();
  });
  it("does not render when missing content", () => {
    render(
      <PreviewURL
        {...experiment}
        referenceBranch={null}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />,
    );

    expect(screen.queryByText("Preview URL")).toBeNull();
  });
  it("shows the correct preview URL LIVE", () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />,
    );

    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=control",
      ),
    ).toBeInTheDocument();
  });
  it("shows the correct preview URL PREVIEW", () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.PREVIEW })}
      />,
    );

    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=control&optin_collection=nimbus-preview",
      ),
    ).toBeInTheDocument();
  });
  it("should update the preview URL", async () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />,
    );

    await selectEvent.select(screen.getByLabelText("Selected Branch"), [
      "treatment",
    ]);

    expect(
      screen.queryByText(
        "about:studies?optin_slug=preview-url-slug&optin_branch=treatment",
      ),
    ).toBeInTheDocument();
  });
  it("should copy to clipboard", async () => {
    render(
      <PreviewURL
        {...experiment}
        status={mockGetStatus({ status: NimbusExperimentStatus.LIVE })}
      />,
    );
    const previewArea = await screen.findByText(
      "about:studies?optin_slug=preview-url-slug&optin_branch=control",
    );
    fireEvent.click(previewArea);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "about:studies?optin_slug=preview-url-slug&optin_branch=control",
    );
  });
});
