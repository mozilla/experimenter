/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  mockAnalysis,
  mockAnalysisOnlyGuardrailsNoDau,
  mockIncompleteAnalysis,
  MOCK_METADATA_WITH_CONFIG,
} from "src/lib/visualization/mocks";
import {
  getControlBranchName,
  getSortedBranchNames,
  shouldUseDou,
} from "src/lib/visualization/utils";

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
      getSortedBranchNames(
        mockAnalysis({ overall: { enrollments: { all: MOCK_OVERALL } } }),
      ),
    ).toEqual(["fum", "fee", "fi", "fo", "englishman"]);
  });

  it("accounts for external config control branch override with many branches", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({
          overall: { enrollments: { all: MOCK_OVERALL } },
          metadata: { external_config: { reference_branch: "englishman" } },
        }),
      ),
    ).toEqual(["englishman", "fee", "fi", "fo", "fum"]);
  });
});

describe("getControlBranchName", () => {
  const MOCK_ANALYSIS_NO_BRANCH_INFO = {
    weekly: { enrollments: { all: {} } },
    overall: { enrollments: { all: {} } },
    show_analysis: true,
    errors: { experiment: [] },
  };

  it("throws an error if it cannot find a branch in the results", () => {
    expect(() =>
      getControlBranchName({
        ...MOCK_ANALYSIS_NO_BRANCH_INFO,
      }),
    ).toThrow("no branch name");
  });
});

describe("shouldUseDou", () => {
  it("returns true if DAU is empty and DOU results exist", () => {
    const useDou = shouldUseDou(
      mockAnalysisOnlyGuardrailsNoDau().overall.enrollments.all.control,
    );
    expect(useDou).toBe(true);
  });
  it("returns false if both DAU and DOU results exist", () => {
    const useDou = shouldUseDou(mockAnalysis().overall.enrollments.all.control);
    expect(useDou).toBe(false);
  });
  it("returns false if neither DAU and DOU results exist", () => {
    const useDou = shouldUseDou(
      mockIncompleteAnalysis().overall.enrollments.all.control,
    );
    expect(useDou).toBe(false);
  });
  it("returns false if no results exist", () => {
    const useDou = shouldUseDou(undefined);
    expect(useDou).toBe(false);
  });
  it("returns false if results are invalid", () => {
    const results = mockAnalysisOnlyGuardrailsNoDau({
      overall: {
        enrollments: {
          all: {
            control: { branch_data: { other_metrics: { days_of_use: {} } } },
          },
        },
      },
    });
    const useDou = shouldUseDou(results.overall.enrollments.all.control);
    expect(useDou).toBe(false);
  });
});
