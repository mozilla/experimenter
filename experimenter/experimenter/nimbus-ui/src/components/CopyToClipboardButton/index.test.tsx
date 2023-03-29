import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import CopyToClipboardButton from "src/components/CopyToClipboardButton";

Object.assign(navigator, {
  clipboard: {
    writeText: () => {},
  },
});

describe("CopyToClipboardButton", () => {
  const originalClipboard = navigator.clipboard.writeText;

  it("should render the component correctly", () => {
    const textToCopy = "Hello, world!";
    const { getByTestId } = render(
      <CopyToClipboardButton text={textToCopy} />
    );

    const button = getByTestId("copy-button");
    expect(button).toBeInTheDocument();

    const icon = button.querySelector(".copy-to-clipboard-icon");
    expect(icon).toBeInTheDocument();
  });

  
  it("should copy text to clipboard when the button is clicked", async () => {
    const textToCopy = "Hello, world!";
    const writeTextMock = jest.fn();
    navigator.clipboard.writeText = writeTextMock;

    const { getByTestId } = render(
      <CopyToClipboardButton text={textToCopy} />
    );

    const button = getByTestId("copy-button");

    fireEvent.click(button);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(textToCopy);

    navigator.clipboard.writeText = originalClipboard;
  });

  it("should show the 'Copied!' tooltip when text is copied", async () => {
    const textToCopy = "Hello, world!";
    navigator.clipboard.writeText = jest.fn();

    const { getByTestId, getByText, queryByText } = render(
      <CopyToClipboardButton text={textToCopy} />
    );
    const button = getByTestId("copy-button");

    fireEvent.click(button);

    await waitFor(() =>
      expect(screen.getByText("Copied!")).toBeInTheDocument(),
    );

    // Wait for the tooltip to disappear
    await new Promise((resolve) => setTimeout(resolve, 3000));

    expect(queryByText("Copied!")).not.toBeInTheDocument();
  });


});
