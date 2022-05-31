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
import { act } from "@testing-library/react-hooks";
import React from "react";
import selectEvent from "react-select-event";
import PageHome from ".";
import { REFETCH_DELAY } from "../../hooks";
import {
  mockDirectoryExperiments,
  mockDirectoryExperimentsQuery,
} from "../../lib/mocks";
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

  it("displays no experiments text when none are found", async () => {
    await renderAndWaitForLoaded([]);
    expect(screen.queryByText("No experiments found.")).toBeInTheDocument();
  });

  const findTabs = () =>
    [
      ["review", screen.getByText("Review (1)")],
      ["preview", screen.getByText("Preview (1)")],
      ["completed", screen.getByText("Completed (4)")],
      ["drafts", screen.getByText("Draft (3)")],
      ["live", screen.getByText("Live (3)")],
      ["archived", screen.getByText("Archived (1)")],
    ] as const;

  it("displays five Directory Tables (one for each status type)", async () => {
    await renderAndWaitForLoaded();
    expect(screen.queryAllByTestId("DirectoryTable")).toHaveLength(6);
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

  it("renders the error warning and refetches when an error occurs querying experiments", async () => {
    jest.useFakeTimers();
    const experiments = mockDirectoryExperiments();
    const mock = mockDirectoryExperimentsQuery(experiments);
    const mockWithError = { ...mock, error: new Error("boop") };

    render(
      <RouterSlugProvider mocks={[mockWithError, mock]}>
        <>
          <CurrentLocation />
          <PageHome {...{ experiments }} />
        </>
      </RouterSlugProvider>,
    );

    await screen.findByTestId("refetch-alert");
    expect(
      screen.queryByText("5 seconds", { exact: false }),
    ).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(REFETCH_DELAY);
    });

    // error is hidden when refetching works as expected
    await screen.findByText("Draft (3)");
    expect(screen.queryByTestId("refetch-alert")).not.toBeInTheDocument();
    expect(screen.queryByTestId("apollo-error-alert")).not.toBeInTheDocument();
  });

  // TODO: not exhaustively testing all filters here, might be worth adding more?
  // Filtering itself is more fully covered in filterExperiments.test.tsx
  it("supports filtering by feature", async () => {
    await renderAndWaitForLoaded();
    const expectedFeatureConfigName = "Picture-in-Picture";
    await selectEvent.select(screen.getByLabelText("Feature"), [
      expectedFeatureConfigName,
    ]);
    await waitFor(() => {
      const featureConfigNames = screen
        .getAllByTestId("directory-feature-config-name")
        .map((el) => el.textContent);
      expect(
        featureConfigNames.every((name) => name === expectedFeatureConfigName),
      ).toBeTruthy();
    });
  });

  it("renders the report button", async () => {
    await renderAndWaitForLoaded();
    expect(screen.queryByText("Reporting")).toBeInTheDocument();
  });

  it("report button renders and fetches api", async () => {
    await renderAndWaitForLoaded();
    const path = "/api/v5/csv";
    const anchor = screen.queryByTestId("reporting-anchor");
    expect(anchor).toHaveAttribute("href", `${path}`);
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
