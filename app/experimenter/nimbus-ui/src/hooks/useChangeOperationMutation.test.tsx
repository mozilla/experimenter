/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { act, renderHook, RenderResult } from "@testing-library/react-hooks";
import React from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../gql/experiments";
import {
  MockedCache,
  mockExperiment,
  mockExperimentMutation,
} from "../lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../types/globalTypes";
import { useChangeOperationMutation } from "./useChangeOperationMutation";

describe("hooks/useChangeOperationMutation", () => {
  it("can successfully execute mutation set callbacks", async () => {
    const { result } = setupTestHook();
    const callbackCount = result.current.callbacks.length;
    const expectedIsLoading = [false];
    for (let idx = 0; idx < callbackCount; idx++) {
      await act(result.current.callbacks[idx]);
      expectedIsLoading.push(true, true, false);
    }
    assertHookStates(result, expectedIsLoading);
  });

  it("indicates when loading mutation", async () => {
    const { result } = setupTestHook();
    await act(result.current.callbacks[0]);
    assertHookStates(result, [false, true, true, false]);
  });

  it("indicates when loading refetch", async () => {
    const refetchState = { called: false, resolved: false };
    const refetch = () => {
      refetchState.called = true;
      return new Promise((resolve) => {
        refetchState.resolved = true;
        resolve(null);
      });
    };
    const { result } = setupTestHook(refetch);
    await act(result.current.callbacks[0]);
    expect(refetchState).toEqual({ called: true, resolved: true });
    assertHookStates(result, [false, true, true, false]);
  });
});

function assertHookStates(
  result: RenderResult<ReturnType<typeof useChangeOperationMutation>>,
  expectedIsLoading: Array<boolean>,
) {
  expect(result.all.length).toEqual(expectedIsLoading.length);
  for (let idx = 0; idx < expectedIsLoading.length; idx++) {
    const step = result.all[idx];
    if (step instanceof Error) {
      fail(`unexpected error in hook: ${step}`);
    }
    expect(step.isLoading).toEqual(expectedIsLoading[idx]);
    expect(step.submitError).toBeNull();
  }
}

const setupTestHook = (refetch?: () => Promise<unknown>) => {
  const experiment = mockExperiment();
  const mutationSets = [
    {
      statusNext: NimbusExperimentStatusEnum.COMPLETE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
    },
    {
      status: NimbusExperimentStatusEnum.LIVE,
    },
    {
      status: NimbusExperimentStatusEnum.DRAFT,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
    },
  ];

  const mocks = mutationSets.reduce<MockedResponse[]>((acc, cur) => {
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

  return renderHook(
    () => useChangeOperationMutation(experiment, refetch, ...mutationSets),
    {
      wrapper,
      initialProps: { mocks },
    },
  );
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
