/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render } from "@testing-library/react";
import { Subject, MOCK_EXPERIMENT } from "./mocks";
import { MOCK_CONFIG } from "../../lib/mocks";

describe("FormAudience", () => {
  it("renders without error", () => {
    render(<Subject />);
  });

  it("renders without error with a partial experiment", () => {
    render(
      <Subject
        config={{
          ...MOCK_CONFIG,
          targetingConfigSlug: [
            { __typename: "NimbusLabelValueType", label: null, value: null },
          ],
        }}
        experiment={{
          ...MOCK_EXPERIMENT,
          firefoxMinVersion: null,
          targetingConfigSlug: null,
          populationPercent: null,
          proposedEnrollment: null,
          proposedDuration: null,
        }}
      />,
    );
  });
});
