/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import Summary from ".";
import { NimbusExperimentStatus } from "../../types/globalTypes";

describe("Summary", () => {
  it("renders expected components", () => {
    const { data } = mockExperimentQuery("demo-slug");
    render(<Subject experiment={data!} />);
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
  });

  describe("JSON representation link", () => {
    it("renders in non-draft status", () => {
      const { data } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.COMPLETE,
      });
      render(<Subject experiment={data!} />);
      expect(screen.getByTestId("link-json")).toBeInTheDocument();
      expect(screen.getByTestId("link-json")).toHaveAttribute(
        "href",
        "/api/v6/experiments/demo-slug/",
      );
    });
  });

  it("does not render in draft status", () => {
    const { data } = mockExperimentQuery("demo-slug");
    render(<Subject experiment={data!} />);
    expect(screen.queryByTestId("link-json")).not.toBeInTheDocument();
  });
});

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <MockedCache>
    <Summary {...{ experiment }} />
  </MockedCache>
);
