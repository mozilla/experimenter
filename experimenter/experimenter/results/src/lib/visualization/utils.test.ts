/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { mockExperiment } from "src/lib/mocks";
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
    expect(getSortedBranchNames(mockAnalysis(), mockExperiment())).toEqual([
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
        mockExperiment(),
      ),
    ).toEqual(["treatment", "control"]);
  });

  it("returns a list of branch names with many branches, the control branch first", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({ overall: { enrollments: { all: MOCK_OVERALL } } }),
        mockExperiment({
          referenceBranch: {
            id: 123,
            name: "User-centric mobile solution",
            slug: "fum",
            description:
              "Behind almost radio result personal none future current.",
            ratio: 1,
            featureValues: [
              {
                featureConfig: { id: 1 },
                value: '{"environmental-fact": "really-citizen"}',
              },
            ],
            screenshots: [],
          },
          treatmentBranches: [
            {
              id: 456,
              name: "Managed zero tolerance projection",
              slug: "fee",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
            {
              id: 4,
              name: "Managed zero tolerance projection",
              slug: "fi",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
            {
              id: 5,
              name: "Managed zero tolerance projection",
              slug: "fo",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
            {
              id: 6,
              name: "Managed zero tolerance projection",
              slug: "englishman",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
          ],
        }),
      ),
    ).toEqual(["fum", "fee", "fi", "fo", "englishman"]);
  });

  it("accounts for external config control branch override and ignores extraneous analysis branches", () => {
    expect(
      getSortedBranchNames(
        mockAnalysis({
          overall: { enrollments: { all: MOCK_OVERALL } },
          metadata: { external_config: { reference_branch: "englishman" } },
        }),
        mockExperiment({
          referenceBranch: {
            id: 123,
            name: "User-centric mobile solution",
            slug: "fee",
            description:
              "Behind almost radio result personal none future current.",
            ratio: 1,
            featureValues: [
              {
                featureConfig: { id: 1 },
                value: '{"environmental-fact": "really-citizen"}',
              },
            ],
            screenshots: [],
          },
          treatmentBranches: [
            {
              id: 456,
              name: "Managed zero tolerance projection",
              slug: "englishman",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
            {
              id: 4,
              name: "Managed zero tolerance projection",
              slug: "fi",
              description: "Next ask then he in degree order.",
              ratio: 1,
              featureValues: [
                {
                  featureConfig: { id: 1 },
                  value: '{"effect-effect-whole": "close-teach-exactly"}',
                },
              ],
              screenshots: [],
            },
          ],
        }),
      ),
    ).toEqual(["englishman", "fee", "fi"]);
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
