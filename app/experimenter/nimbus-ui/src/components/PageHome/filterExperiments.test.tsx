/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MOCK_CONFIG } from "../../lib/mocks";
import filterExperiments, {
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "./filterExperiments";
import {
  DEFAULT_OPTIONS,
  EVERYTHING_SELECTED_VALUE,
  MOCK_EXPERIMENTS,
} from "./mocks";
import { filterValueKeys } from "./types";

const { owners, applications, featureConfigs } = MOCK_CONFIG!;

describe("getFilterValueFromParams", () => {
  it("converts comma-separated list representation from filter params into a filter value", () => {
    const params = new URLSearchParams();
    params.set("owners", "alpha-example@mozilla.com,beta-example@mozilla.com");
    params.set("applications", "DESKTOP,FENIX");
    params.set("featureConfigs", "IOS:foo-lila-sat");
    expect(getFilterValueFromParams(MOCK_CONFIG, params)).toEqual({
      owners: [owners![0], owners![1]],
      applications: [applications![0], applications![3]],
      featureConfigs: [featureConfigs![2]],
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
      featureConfigs: [featureConfigs![2], featureConfigs![3]],
    });
    expect(params.get("owners")).toEqual(
      "alpha-example@mozilla.com,beta-example@mozilla.com",
    );
    expect(params.get("applications")).toEqual("DESKTOP,FENIX");
    expect(params.get("featureConfigs")).toEqual(
      "IOS:foo-lila-sat,FENIX:foo-lila-sat",
    );
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
      MOCK_EXPERIMENTS.filter((e) => (e.featureConfigs?.length ?? 0) > 0),
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
          case "featureConfigs":
            expect(experiment.featureConfigs).toEqual([
              MOCK_CONFIG!.featureConfigs![0]!,
            ]);
            break;
          case "firefoxVersions":
            expect(experiment.firefoxMinVersion).toEqual(
              MOCK_CONFIG!.firefoxVersions![0]!.value,
            );
            break;
        }
      }
    }
  });
});
