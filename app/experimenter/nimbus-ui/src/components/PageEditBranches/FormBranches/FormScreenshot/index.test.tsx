/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { Subject } from "./mocks";

describe("FormScreenshot", () => {
  const expectedImageUrl = "http://example.com/image.PNG";
  beforeEach(() => {
    global.URL.createObjectURL = jest.fn((file) => expectedImageUrl);
  });

  it("accepts description edit, image upload, and displays preview", async () => {
    const fieldNamePrefix = "referenceBranch.screenshots[0]";
    const watcher = jest.fn();

    render(
      <Subject
        {...{
          defaultValues: { image: null },
          fieldNamePrefix,
          watcher,
        }}
      />,
    );

    const expectedDescription = "changed";
    const expectedFile = new File(["pretend this is an image"], "Capture.PNG", {
      type: "image/png",
    });

    fireEvent.change(screen.getByTestId(`${fieldNamePrefix}.description`), {
      target: { value: expectedDescription },
    });
    fireEvent.change(screen.getByLabelText("Image"), {
      target: { files: [expectedFile] },
    });

    await waitFor(() => {
      const [lastFormChange] = watcher.mock.calls.slice(-1);
      const formData = lastFormChange[0]?.referenceBranch?.screenshots?.[0];
      expect(formData).toEqual({
        description: expectedDescription,
        image: expectedFile,
      });
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(expectedFile);
      expect(screen.getByTestId("upload-preview")).toHaveAttribute(
        "src",
        expectedImageUrl,
      );
    });
  });

  it("does not render a preview with a null image", () => {
    render(
      <Subject
        {...{
          defaultValues: { image: null },
        }}
      />,
    );
    expect(screen.queryByTestId("upload-label")).toHaveTextContent("");
    expect(screen.queryByTestId("upload-preview")).not.toBeInTheDocument();
  });

  it("does not render a preview with a non-File image", () => {
    render(
      <Subject
        {...{
          defaultValues: { image: {} },
        }}
      />,
    );
    expect(screen.queryByTestId("upload-label")).toHaveTextContent("");
    expect(screen.queryByTestId("upload-preview")).not.toBeInTheDocument();
  });

  it("displays a preview of existing screenshot image", () => {
    const expectedUrl = "https://example.com/existing.PNG";
    render(
      <Subject
        {...{
          defaultValues: { image: expectedUrl },
        }}
      />,
    );
    expect(screen.queryByTestId("upload-label")).toHaveTextContent(expectedUrl);
    expect(screen.queryByTestId("upload-preview")).toHaveAttribute(
      "src",
      expectedUrl,
    );
  });
});
