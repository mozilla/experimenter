/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import {
  default as SearchBar,
  resetWindowLocation,
} from "src/components/PageHome/SearchBar";
import { mockDirectoryExperimentsQuery } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";

describe("SearchBar", () => {
  it("renders as expected", async () => {
    const onChange = jest.fn();
    render(<Subject experiments={[]} onChange={onChange} />);
    const searchInput = screen.getByTestId("SearchExperiments");

    // search input present without clear icon
    expect(searchInput).toBeInTheDocument();
    expect(
      screen.queryByTestId("ClearSearchExperiments"),
    ).not.toBeInTheDocument();

    // once user type something, clear icon will be visible
    userEvent.type(searchInput, "other");
    await waitFor(() => {
      expect(searchInput).toHaveValue("other");
    });
    const clear = screen.getByTestId("ClearSearchExperiments");
    expect(clear).toBeInTheDocument();

    // once user click on clear, search input will be empty and clear icon will disappear
    fireEvent.click(clear);
    expect(
      screen.queryByTestId("ClearSearchExperiments"),
    ).not.toBeInTheDocument();
    await waitFor(() => {
      expect(searchInput).toHaveValue("");
    });
  });
  it("calls resetWindowLocation when nimbus-ui-search is not in localStorage", () => {
    const resetWindowLocation = jest.fn();
    // jest.spyOn(Subject.prototype, 'resetWindowLocation').mockImplementation(resetWindowLocation);

    jest.spyOn(window, "localStorage", "get").mockReturnValue({});

    const formRef = { current: {} };

    render(<Subject experiments={[]} onChange={formRef} />);

    expect(resetWindowLocation).toHaveBeenCalledTimes(1);
  });
});

describe("resetWindowLocation", () => {
  it("resets window location to default homepage", () => {
    // Mock the window.location object

    global.window = Object.create(window);
    global.window.location = {
      search: "?query=test",
    };

    // Call the function
    resetWindowLocation();

    // Expect window.location to be updated
    expect(window.location.search).toBe("");
  });
});

const Subject = ({
  experiments,
  onChange,
}: {
  experiments: getAllExperiments_experiments[];
  onChange: any;
}) => (
  <RouterSlugProvider mocks={[mockDirectoryExperimentsQuery(experiments)]}>
    <>
      <SearchBar onChange={onChange} {...{ experiments }} />
    </>
  </RouterSlugProvider>
);
