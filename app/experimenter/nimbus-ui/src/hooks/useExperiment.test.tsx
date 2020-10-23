/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, waitFor } from "@testing-library/react";
import { useExperiment } from "./useExperiment";
import { MockedCache, mockExperimentQuery } from "../lib/mocks";

describe("hooks/useExperiment", () => {
  describe("useExperiment", () => {
    let hook: ReturnType<typeof useExperiment>;

    const TestExperiment = ({ slug }: { slug: string }) => {
      hook = useExperiment(slug);
      return <p>Notre-Dame-du-Bon-Conseil, QC</p>;
    };

    it("returns the experiment", async () => {
      const { mock, data } = mockExperimentQuery("howdy");

      render(
        <MockedCache mocks={[mock]}>
          <TestExperiment slug="howdy" />
        </MockedCache>,
      );

      await waitFor(() => expect(hook.experiment).toEqual(data));
    });
  });
});
