import { cleanup } from "@testing-library/react";
import React from "react";

import App from "experimenter-rapid/components/App";

afterEach(cleanup);

describe("<App />", () => {
  it("root route shows link to create page", () => {
    const { getByText } = renderWithRouter(<App />);
    expect(getByText("Create a new experiment")).toBeInTheDocument();
  });

  it("unknown route shows 404 message", () => {
    const { getByText } = renderWithRouter(<App />, {
      route: "/a/route/that/does/not/exist/",
    });
    expect(getByText("404")).toBeInTheDocument();
  });

  it("includes the experiment form page at `/new/`", () => {
    const { getByText } = renderWithRouter(<App />, {
      route: "/new/",
    });
    expect(getByText("Create a New A/A Experiment")).toBeInTheDocument();
  });
});
