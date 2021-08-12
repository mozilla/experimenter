/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { act, renderHook } from "@testing-library/react-hooks";
import React from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../gql/experiments";
import { SUBMIT_ERROR } from "../lib/constants";
import {
  MockedCache,
  mockExperiment,
  mockExperimentMutation,
} from "../lib/mocks";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { ExperimentInput } from "../types/globalTypes";
import { ARCHIVING_EXPERIMENT, useArchive } from "./useArchive";

describe("hooks/useArchive", () => {
  const experiment = mockExperiment();

  it("handles success", async () => {
    const refetch = jest.fn();
    const { result } = setupTestHook(
      experiment,
      refetch,
      "updateExperiment",
      {
        id: experiment.id,
        isArchived: true,
        changelogMessage: ARCHIVING_EXPERIMENT,
      },
      {
        message: "success",
      },
    );
    await act(result.current.callback);
    expect(result.current.isLoading).toEqual(false);
    expect(result.current.submitError).toBeNull();
    expect(refetch).toHaveBeenCalled();
  });

  it("handles error message", async () => {
    const refetch = jest.fn();
    const { result } = setupTestHook(
      experiment,
      refetch,
      "updateExperiment",
      {
        id: experiment.id,
        isArchived: true,
        changelogMessage: ARCHIVING_EXPERIMENT,
      },
      {
        message: { isArchived: "something wrong" },
      },
    );
    await act(result.current.callback);
    expect(result.current.isLoading).toEqual(false);
    expect(result.current.submitError).toEqual(
      '{"isArchived":"something wrong"}',
    );
    expect(refetch).not.toHaveBeenCalled();
  });

  it("handles missing response", async () => {
    const refetch = jest.fn();
    const { result } = setupTestHook(
      experiment,
      refetch,
      "missingResponse",
      {
        id: experiment.id,
        isArchived: true,
        changelogMessage: ARCHIVING_EXPERIMENT,
      },
      {
        message: { isArchived: "something wrong" },
      },
    );
    await act(result.current.callback);
    expect(result.current.isLoading).toEqual(false);
    expect(result.current.submitError).toEqual(SUBMIT_ERROR);

    expect(refetch).not.toHaveBeenCalled();
  });
});

export const setupTestHook = (
  experiment: Partial<getExperiment_experimentBySlug>,
  refetch: () => Promise<unknown>,
  mutationResponseName: string,
  input: ExperimentInput,
  response: {
    message: string | Record<string, any>;
  },
) => {
  const mock = mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    input,
    mutationResponseName,
    response,
  );

  return renderHook(() => useArchive(experiment, refetch), {
    wrapper,
    initialProps: { mocks: [mock] },
  });
};

export const wrapper = ({
  mocks,
  children,
}: {
  mocks?: MockedResponse[];
  children?: React.ReactNode;
}) => (
  <MockedCache {...{ mocks }}>{children as React.ReactElement}</MockedCache>
);
