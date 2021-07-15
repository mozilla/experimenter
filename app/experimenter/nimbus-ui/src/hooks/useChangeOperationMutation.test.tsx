/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { renderHook } from "@testing-library/react-hooks";
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
    const { result, invokeCallback, waitForNextUpdate } = setupTestHook();

    const callbackCount = result.current.callbacks.length;
    for (let idx = 0; idx < callbackCount; idx++) {
      invokeCallback(idx);

      await waitForNextUpdate();
      expect(result.current.isLoading).toBeTruthy();

      await waitForNextUpdate();
      expect(result.current.isLoading).toBeFalsy();
      expect(result.current.submitError).toBeNull();
    }
  });

  it("indicates when loading mutation", async () => {
    const { result, invokeCallback, waitForNextUpdate } = setupTestHook();
    expect(result.current.isLoading).toBeFalsy();
    invokeCallback();

    await waitForNextUpdate();
    expect(result.current.isLoading).toBeTruthy();

    await waitForNextUpdate();
    expect(result.current.isLoading).toBeFalsy();
  });

  it("indicates when loading refetch", async () => {
    const refetchState = {
      called: false,
      resolve: null as null | (() => void),
    };
    const refetch = () => {
      refetchState.called = true;
      return new Promise(
        (resolve) => (refetchState.resolve = () => resolve(null)),
      );
    };

    const { result, invokeCallback, waitForNextUpdate } =
      setupTestHook(refetch);
    expect(result.current.isLoading).toBeFalsy();
    invokeCallback();

    await waitForNextUpdate();
    expect(refetchState.called).toBeFalsy();
    expect(result.current.isLoading).toBeTruthy();

    await waitForNextUpdate();
    expect(refetchState.called).toBeTruthy();
    expect(result.current.isLoading).toBeTruthy();

    expect(refetchState.resolve).not.toBeNull();
    refetchState.resolve!();

    await waitForNextUpdate();
    expect(result.current.isLoading).toBeFalsy();
  });
});

const setupTestHook = (refetch?: () => Promise<unknown>) => {
  const experiment = mockExperiment();
  const mutationSets = [
    {
      statusNext: NimbusExperimentStatus.COMPLETE,
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

  const { result, waitForNextUpdate } = renderHook(
    () => useChangeOperationMutation(experiment, refetch, ...mutationSets),
    {
      wrapper,
      initialProps: { mocks },
    },
  );

  const invokeCallback = (callbackIdx = 0) =>
    setTimeout(() => result.current.callbacks[callbackIdx](), 0.1);

  return {
    result,
    invokeCallback,
    waitForNextUpdate,
    mutationSets,
    refetch,
  };
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
