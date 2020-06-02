import { render } from "@testing-library/react";
import React from "react";

import App from "experimenter-rapid/components/App";

describe("<App />", () => {
  it("has placeholder text", async () => {
    const { getByText } = await render(<App />);
    expect(getByText("Rapid Experiments")).toBeInTheDocument();
  });
});
