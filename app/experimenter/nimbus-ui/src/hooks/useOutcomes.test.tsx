/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { renderHook } from "@testing-library/react-hooks";
import React from "react";
import { useOutcomes } from ".";
import {
  MockedCache,
  mockExperimentQuery,
  mockOutcomeSets,
} from "../lib/mocks";

describe("hooks/useOutcomes", () => {
  it("matches experiment outcome slugs to available configuration outcomes", () => {
    const { mock, experiment } = mockExperimentQuery("howdy");
    const mockedSets = mockOutcomeSets(experiment);
    const { result } = renderHook(() => useOutcomes(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    expect(result.current.primaryOutcomes).toStrictEqual(
      mockedSets.primaryOutcomes,
    );
    expect(result.current.secondaryOutcomes).toStrictEqual(
      mockedSets.secondaryOutcomes,
    );
  });

  it("returns empty arrays when no slugs match configuration outcomes", () => {
    const { mock, experiment } = mockExperimentQuery("howdy", {
      primaryOutcomes: ["the bird"],
      secondaryOutcomes: ["the worm"],
    });
    const { result } = renderHook(() => useOutcomes(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    expect(result.current.primaryOutcomes).toStrictEqual([]);
    expect(result.current.secondaryOutcomes).toStrictEqual([]);
  });

  it("returns empty arrays when the slug arrays are actually null", () => {
    const { mock, experiment } = mockExperimentQuery("howdy", {
      primaryOutcomes: null,
      secondaryOutcomes: null,
    });
    const { result } = renderHook(() => useOutcomes(experiment), {
      wrapper,
      initialProps: { mocks: [mock] },
    });

    expect(result.current.primaryOutcomes).toStrictEqual([]);
    expect(result.current.secondaryOutcomes).toStrictEqual([]);
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
