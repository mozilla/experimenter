/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render } from "@testing-library/react";
import HeaderEditExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";

const { data } = mockExperimentQuery("demo-slug");

describe("HeaderEditExperiment", () => {
  it("renders as expected", () => {
    render(
      <HeaderEditExperiment
        name={data!.name}
        slug={data!.slug}
        status={data!.status}
      />,
    );
    expect(screen.getByTestId("header-experiment-name")).toHaveTextContent(
      "Open-architected background installation",
    );
    expect(screen.getByTestId("header-experiment-slug")).toHaveTextContent(
      "demo-slug",
    );
    expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
      "DRAFT",
    );
  });
});
