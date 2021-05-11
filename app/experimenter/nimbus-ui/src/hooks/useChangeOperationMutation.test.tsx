/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { waitFor } from "@testing-library/dom";
import { act, renderHook } from "@testing-library/react-hooks";
import React from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../gql/experiments";
import {
  MockedCache,
  mockExperiment,
  mockExperimentMutation,
} from "../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../types/globalTypes";
import { useChangeOperationMutation } from "./useChangeOperationMutation";

describe("hooks/useChangeOperationMutation", () => {
  it("can successfully execute mutation set callbacks", async () => {
    const { callbacks, submitError } = setupTestHook();

    for (const callback of callbacks) {
      await act(async () => void callback());
      await waitFor(() => expect(submitError).toBeNull());
    }
  });

  it("indicates when loading", async () => {
    const {
      isLoading,
      callbacks: [callback],
    } = setupTestHook();
    expect(isLoading).toBeFalsy();
    await act(async () => void callback());
    waitFor(() => expect(isLoading).toBeTruthy());
  });
});

const setupTestHook = (customMocks: MockedResponse[] = []) => {
  const experiment = mockExperiment();
  const refetch = jest.fn();
  const mutationSets = [
    {
      isEndRequested: true,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    },
    {
      status: NimbusExperimentStatus.LIVE,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    },
  ];

  const mocks = customMocks.length
    ? customMocks
    : mutationSets.reduce<MockedResponse[]>((acc, cur) => {
        return acc.concat(
          mockExperimentMutation(
            UPDATE_EXPERIMENT_MUTATION,
            {
              id: experiment.id,
              ...cur,
            },
            "updateExperiment",
            {
              experiment: {
                ...cur,
              },
            },
          ),
        );
      }, []);

  const {
    result: {
      current: { isLoading, submitError, callbacks },
    },
  } = renderHook(
    () => useChangeOperationMutation(experiment, refetch, ...mutationSets),
    {
      wrapper,
      initialProps: { mocks },
    },
  );

  return { isLoading, submitError, callbacks, mutationSets, refetch };
};

const wrapper = ({
  mocks = [],
  children,
}: {
  mocks?: MockedResponse[];
  children?: React.ReactNode;
}) => (
  <MockedCache {...{ mocks }}>{children as React.ReactElement}</MockedCache>
);
