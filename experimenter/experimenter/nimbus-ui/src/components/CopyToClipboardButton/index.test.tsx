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
    render(<CopyToClipboardButton text={textToCopy} />);

    const button = screen.getByTestId("copy-button");
    expect(button).toBeInTheDocument();

    const icon = screen.getByTestId("copy-to-clipboard-icon");
    expect(icon).toBeInTheDocument();
  });

  it("should copy text to clipboard when the button is clicked", async () => {
    const textToCopy = "Hello, world!";
    const writeTextMock = jest.fn();
    navigator.clipboard.writeText = writeTextMock;

    render(<CopyToClipboardButton text={textToCopy} />);

    const button = screen.getByTestId("copy-button");

    fireEvent.click(button);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(textToCopy);

    navigator.clipboard.writeText = originalClipboard;
  });

  it("should log error and show the 'Failed to copy slug' tooltip when copy fails", async () => {
    const textToCopy = "Hello, world!";
    const writeTextMock = jest
      .fn()
      .mockRejectedValue(new Error("Failed to copy slug"));
    navigator.clipboard.writeText = writeTextMock;

    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    render(<CopyToClipboardButton text={textToCopy} />);

    const button = screen.getByTestId("copy-button");
    fireEvent.click(button);

    await waitFor(() => expect(writeTextMock).toHaveBeenCalled());

    await waitFor(() =>
      expect(screen.getByText("Failed to copy slug")).toBeInTheDocument(),
    );

    // Wait for the tooltip to disappear
    await new Promise((resolve) => setTimeout(resolve, 3000));

    expect(screen.queryByText("Failed to copy slug")).not.toBeInTheDocument();

    expect(consoleSpy).toHaveBeenCalledWith(new Error("Failed to copy slug"));

    consoleSpy.mockRestore();
    navigator.clipboard.writeText = originalClipboard;
  });

  it("should scale up on mouse over and scale back to normal on mouse out", () => {
    const textToCopy = "Hello, world!";
    render(<CopyToClipboardButton text={textToCopy} />);
    const icon = screen.getByTestId("copy-to-clipboard-icon");

    fireEvent.mouseOver(icon);
    expect(icon.style.transform).toBe("scale(1.2)");

    fireEvent.mouseOut(icon);
    expect(icon.style.transform).toBe("scale(1)");
  });

  it("should show the 'Copied to clipboard!' tooltip when text is copied", async () => {
    const textToCopy = "Hello, world!";
    navigator.clipboard.writeText = jest.fn();

    render(<CopyToClipboardButton text={textToCopy} />);
    const button = screen.getByTestId("copy-button");

    fireEvent.click(button);

    await waitFor(() =>
      expect(screen.getByText("Copied to clipboard!")).toBeInTheDocument(),
    );

    // Wait for the tooltip to disappear
    await new Promise((resolve) => setTimeout(resolve, 3000));

    expect(screen.queryByText("Copied to clipboard!")).not.toBeInTheDocument();
  });
});
