/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { mockAnalysis, MOCK_METADATA_WITH_CONFIG } from "./mocks";
import { getControlBranchName, getSortedBranchNames } from "./utils";

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
      getSortedBranchNames(mockAnalysis({ overall: { all: MOCK_OVERALL } })),
    ).toEqual(["fum", "fee", "fi", "fo", "englishman"]);
  });

  it("accounts for external config control branch override with many branches", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({
          overall: { all: MOCK_OVERALL },
          metadata: { external_config: { reference_branch: "englishman" } },
        }),
      ),
    ).toEqual(["englishman", "fee", "fi", "fo", "fum"]);
  });
});

describe("getControlBranchName", () => {
  const MOCK_ANALYSIS_DAILY = {
    daily: {
      all: [
        {
          point: 1,
          branch: "test",
          metric: "test_metric",
          statistic: "count",
        },
      ],
    },
    weekly: { all: {} },
    overall: { all: {} },
    show_analysis: true,
    errors: { experiment: [] },
  };

  it("returns the branch from daily if there are no other branches", () => {
    expect(getControlBranchName(MOCK_ANALYSIS_DAILY)).toEqual("test");
  });

  it("throws an error if it cannot determine the control branch and there are multiple branches in daily", () => {
    expect(() =>
      getControlBranchName({
        ...MOCK_ANALYSIS_DAILY,
        daily: {
          all: [
            {
              point: 1,
              branch: "test",
              metric: "test_metric",
              statistic: "count",
            },
            {
              point: 11,
              branch: "not-test",
              metric: "test_metric",
              statistic: "binomial",
            },
          ],
        },
      }),
    ).toThrow("no branch name");
  });

  it("throws an error if it cannot find a branch in the results", () => {
    expect(() =>
      getControlBranchName({ ...MOCK_ANALYSIS_DAILY, daily: { all: [] } }),
    ).toThrow("no branch name");
  });
});
