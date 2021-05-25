import "@testing-library/jest-dom/extend-expect";
import { render } from "@testing-library/react";
import Error from "experimenter/components/Error";
import React from "react";

describe("The `Error` component", () => {
  const error = "an error occured!";
  it("renders error message", () => {
    const { getByText } = render(<Error error={error} />);
    expect(getByText(error)).toBeInTheDocument();
  });
});
