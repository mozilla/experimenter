/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import filterExperiments, {
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "src/components/PageHome/filterExperiments";
import {
  DEFAULT_OPTIONS,
  EVERYTHING_SELECTED_VALUE,
  MOCK_EXPERIMENTS,
} from "src/components/PageHome/mocks";
import { filterValueKeys } from "src/components/PageHome/types";
import { MOCK_CONFIG } from "src/lib/mocks";

const {
  owners,
  applications,
  allFeatureConfigs,
  channels,
  types,
  targetingConfigs,
  projects,
} = MOCK_CONFIG!;

describe("getFilterValueFromParams", () => {
  it("converts comma-separated list representation from filter params into a filter value", () => {
    const params = new URLSearchParams();
    params.set("owners", "alpha-example@mozilla.com,beta-example@mozilla.com");
    params.set("applications", "DESKTOP,FENIX");
    params.set("allFeatureConfigs", "IOS:foo-lila-sat");
    params.set("channels", "BETA");
    params.set("types", "EXPERIMENT");
    params.set("projects", "Pocket");
    params.set("targetingConfigs", "MAC_ONLY");

    expect(getFilterValueFromParams(MOCK_CONFIG, params)).toEqual({
      owners: [owners![0], owners![1]],
      applications: [applications![0], applications![3]],
      allFeatureConfigs: [allFeatureConfigs![2]],
      channels: [channels![0]],
      types: [types![0]],
      projects: [projects![0]],
      targetingConfigs: [targetingConfigs![0]],
    });
  });
});

describe("updateParamsFromFilterValue", () => {
  it("sets filter params to comma-separated list representations of filter values", () => {
    const params = new URLSearchParams();
    const updateSearchParams = jest.fn((cb) => cb(params));
    updateParamsFromFilterValue(updateSearchParams, {
      owners: [owners![0], owners![1]],
      applications: [applications![0], applications![3]],
      allFeatureConfigs: [allFeatureConfigs![2], allFeatureConfigs![3]],
      channels: [channels![0], channels![1]],
      types: [types![0], types![1]],
      projects: [projects![0], projects![1]],
      targetingConfigs: [targetingConfigs![0], targetingConfigs![1]],
    });
    expect(params.get("owners")).toEqual(
      "alpha-example@mozilla.com,beta-example@mozilla.com",
    );
    expect(params.get("applications")).toEqual("DESKTOP,FENIX");
    expect(params.get("allFeatureConfigs")).toEqual(
      "IOS:foo-lila-sat,FENIX:foo-lila-sat",
    );
    expect(params.get("channels")).toEqual("BETA,NIGHTLY");
    expect(params.get("types")).toEqual("EXPERIMENT,ROLLOUT");
    expect(params.get("projects")).toEqual("Pocket,Mdn");
    expect(params.get("targetingConfigs")).toEqual("MAC_ONLY,WIN_ONLY");
  });

  it("handles a roundtrip encoding with everything filtered", () => {
    const params = new URLSearchParams();
    const updateSearchParams = jest.fn((cb) => cb(params));
    updateParamsFromFilterValue(updateSearchParams, EVERYTHING_SELECTED_VALUE);
    expect(getFilterValueFromParams(MOCK_CONFIG, params)).toEqual(
      EVERYTHING_SELECTED_VALUE,
    );
  });
});

describe("filterExperiments", () => {
  it("filters nothing if filter value is empty", () => {
    expect(filterExperiments(MOCK_EXPERIMENTS, {})).toEqual(MOCK_EXPERIMENTS);
  });

  it("filters only an empty feature config if filter value has everything", () => {
    expect(
      filterExperiments(MOCK_EXPERIMENTS, EVERYTHING_SELECTED_VALUE),
    ).toEqual(
      MOCK_EXPERIMENTS.filter((e) => (e.featureConfigs?.length || 0) > 0),
    );
  });

  it("filters per individual criteria as expected", () => {
    for (const key of filterValueKeys) {
      const filterValue = {
        [key]: [DEFAULT_OPTIONS[key]![0]!],
      };
      const result = filterExperiments(MOCK_EXPERIMENTS, filterValue);
      for (const experiment of result) {
        switch (key) {
          case "owners":
            expect(experiment.owner).toEqual(MOCK_CONFIG!.owners![0]!);
            break;
          case "applications":
            expect(experiment.application).toEqual(
              MOCK_CONFIG!.applications![0]!.value,
            );
            break;
          case "allFeatureConfigs":
            expect(experiment.featureConfigs).toEqual([
              MOCK_CONFIG!.allFeatureConfigs![0]!,
            ]);
            break;
          case "firefoxVersions":
            expect(experiment.firefoxMinVersion).toEqual(
              MOCK_CONFIG!.firefoxVersions![0]!.value,
            );
            break;
          case "channels":
            expect(experiment.channel).toEqual(
              MOCK_CONFIG!.channels![0]!.value,
            );
            break;
          case "types":
            expect(experiment.isRollout).toEqual(false);
            break;
          case "projects":
            expect(experiment.projects).toEqual([MOCK_CONFIG!.projects![0]!]);
            break;
          case "targetingConfigs":
            expect(experiment.targetingConfig).toEqual([
              MOCK_CONFIG!.targetingConfigs![0]!,
            ]);
            break;
          case "qaStatus":
            expect(experiment.qaStatus).toEqual([MOCK_CONFIG!.qaStatus![0]]);
            break;
        }
      }
    }
  });
});
