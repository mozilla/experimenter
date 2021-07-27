/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as apollo from "@apollo/client";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  waitForElementToBeRemoved,
} from "@testing-library/react";
import React from "react";
import PageHome from ".";
import { mockDirectoryExperimentsQuery } from "../../lib/mocks";
import { CurrentLocation, RouterSlugProvider } from "../../lib/test-utils";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";

describe("PageHome", () => {
  it("renders as expected", () => {
    render(<Subject />);

    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
    expect(screen.getByText("Create new")).toBeInTheDocument();
  });

  it("displays loading when experiments are still loading", () => {
    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      loading: true,
    });

    render(<Subject experiments={[]} />);

    expect(screen.queryByTestId("page-loading")).toBeInTheDocument();
  });

  it("displays loading when experiments are still loading", async () => {
    await renderAndWaitForLoaded([]);
    expect(screen.queryByText("No experiments found.")).toBeInTheDocument();
  });

  it("renders the error alert when an error occurs", () => {
    const error = new Error("You done it now!");

    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      error,
    });

    render(<Subject />);
    expect(screen.queryByTestId("apollo-error-alert")).toBeInTheDocument();
  });

  const findTabs = () =>
    [
      ["review", screen.getByText("Review (1)")],
      ["preview", screen.getByText("Preview (1)")],
      ["completed", screen.getByText("Completed (4)")],
      ["drafts", screen.getByText("Draft (3)")],
      ["live", screen.getByText("Live (3)")],
    ] as const;

  it("displays five Directory Tables (one for each status type)", async () => {
    await renderAndWaitForLoaded();
    expect(screen.queryAllByTestId("DirectoryTable")).toHaveLength(5);
    for (const [tabKey, tab] of findTabs()) {
      expect(tab).toBeInTheDocument();
    }
  });

  it("supports updating search params when tabs are clicked", async () => {
    await renderAndWaitForLoaded();
    for (const [tabKey, tab] of findTabs()) {
      fireEvent.click(tab);
      await waitFor(() => {
        expect(tab).toHaveClass("active");
        expect(screen.getByTestId("location")).toHaveTextContent(
          `tab=${tabKey}`,
        );
      });
    }
  });
});

const Subject = ({
  experiments,
}: {
  experiments?: getAllExperiments_experiments[];
}) => (
  <RouterSlugProvider mocks={[mockDirectoryExperimentsQuery(experiments)]}>
    <>
      <CurrentLocation />
      <PageHome {...{ experiments }} />
    </>
  </RouterSlugProvider>
);

const renderAndWaitForLoaded = async (
  experiments?: getAllExperiments_experiments[],
) => {
  render(<Subject {...{ experiments }} />);
  await waitForElementToBeRemoved(() => screen.getByTestId("page-loading"));
};
