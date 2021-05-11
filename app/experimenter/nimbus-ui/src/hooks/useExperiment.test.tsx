/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react-hooks";
import React from "react";
import { MockedCache, mockExperimentQuery } from "../lib/mocks";
import { useExperiment } from "./useExperiment";

describe("hooks/useExperiment", () => {
  it("starts by loading", async () => {
    const { result } = renderHook(() => useExperiment("howdy"), {
      wrapper,
    });
    expect(result.current.loading).toBeTruthy();
  });

  it("loads the experiment", async () => {
    const { mock, experiment } = mockExperimentQuery("howdy");
    const { result } = renderHook(() => useExperiment(experiment.slug), {
      wrapper,
      initialProps: { mocks: [mock] },
    });
    await waitFor(() => expect(result.current.experiment).toEqual(experiment));
  });

  it("indicates notFound if there's no experiment", async () => {
    const { mock } = mockExperimentQuery("howdy", null);
    const { result } = renderHook(() => useExperiment("howdy"), {
      wrapper,
      initialProps: { mocks: [mock] },
    });
    await waitFor(() => expect(result.current.notFound).toBeTruthy());
  });
});

const wrapper = ({
  mocks = [],
  children,
}: {
  mocks?: MockedResponse[];
  children?: React.ReactNode;
}) => (
  <MockedCache {...{ mocks }}>{children as React.ReactElement}</MockedCache>
);
