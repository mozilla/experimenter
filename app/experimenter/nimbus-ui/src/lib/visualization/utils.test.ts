/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { mockAnalysis, MOCK_METADATA_WITH_CONFIG } from "./mocks";
import { getSortedBranchNames } from "./utils";

describe("getSortedBranchNames", () => {
  const MOCK_OVERALL = {
    fee: {
      is_control: false,
    },
    fi: {
      is_control: false,
    },
    fo: {
      is_control: false,
    },
    fum: {
      is_control: true,
    },
    englishman: {
      is_control: false,
    },
  };

  it("returns a list of branch names, the control branch first", () => {
    expect(getSortedBranchNames(mockAnalysis())).toEqual([
      "control",
      "treatment",
    ]);
  });

  it("accounts for external config control branch override", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({
          metadata: MOCK_METADATA_WITH_CONFIG,
        }),
      ),
    ).toEqual(["treatment", "control"]);
  });

  it("returns a list of branch names with many branches, the control branch first", () => {
    expect(
      getSortedBranchNames(mockAnalysis({ overall: MOCK_OVERALL })),
    ).toEqual(["fum", "fee", "fi", "fo", "englishman"]);
  });

  it("accounts for external config control branch override with many branches", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({
          overall: MOCK_OVERALL,
          metadata: { external_config: { reference_branch: "englishman" } },
        }),
      ),
    ).toEqual(["englishman", "fee", "fi", "fo", "fum"]);
  });
});
