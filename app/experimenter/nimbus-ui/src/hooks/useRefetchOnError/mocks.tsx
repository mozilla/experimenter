/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { useRefetchOnError } from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { useExperiment } from "../useExperiment";

const ComponentWithHook = () => {
  // this works with any GQL query, we just need to provide one with mocks for testing
  const { error, refetch } = useExperiment("demo-slug");
  const ErrorAlert = useRefetchOnError(error, refetch);

  if (error) {
    return ErrorAlert;
  }
  return <p>No errors!</p>;
};

export const Subject = ({ noValidQueries = false }) => {
  const { mock } = mockExperimentQuery("demo-slug");
  const mockWithError = {
    ...mock,
    error: new Error("boop, something's actually wrong"),
  };
  const secondMock = noValidQueries ? mockWithError : mock;

  return (
    <RouterSlugProvider mocks={[mockWithError, secondMock]}>
      <ComponentWithHook />
    </RouterSlugProvider>
  );
};

export default Subject;
