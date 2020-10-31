/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import PageEditContainer from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";

describe("PageRequestReview", () => {
  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditContainer")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toHaveTextContent("Howdy!");
      expect(screen.getByTestId("child")).toBeInTheDocument();
    });
  });

  it("renders not found screen", async () => {
    const { mock: notFoundMock } = mockExperimentQuery("demo-slug", null);
    render(<Subject mocks={[notFoundMock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("not-found")).toBeInTheDocument();
    });
  });

  it("renders loading screen", () => {
    render(<Subject />);
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });
});

const Subject = ({
  mocks = [],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageEditContainer title="Howdy!" testId="PageEditContainer">
      {({ experiment }) => <p data-testid="child">{experiment.slug}</p>}
    </PageEditContainer>
  </RouterSlugProvider>
);
