import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import Error from "experimenter/components/Error";

describe("The `Error` component", () => {
  const error = "an error occured!";
  it("renders error message", () => {
    const { getByText } = render(<Error error={error} />);
    expect(getByText(error)).toBeInTheDocument();
  });
});
