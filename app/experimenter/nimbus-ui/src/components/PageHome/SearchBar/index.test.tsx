/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { default as SearchBar } from ".";
import { mockDirectoryExperimentsQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { getAllExperiments_experiments } from "../../../types/getAllExperiments";

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
