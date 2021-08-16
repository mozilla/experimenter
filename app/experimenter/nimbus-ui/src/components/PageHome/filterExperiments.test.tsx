/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import filterExperiments, {
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "./filterExperiments";
import { EVERYTHING_SELECTED_VALUE, MOCK_EXPERIMENTS } from "./mocks";
import { FilterValue } from "./types";

const MOCK_FILTER_VALUE: FilterValue = {
  owners: ["foo", "bar"],
  application: ["baz", "quux"],
};

describe("getFilterValueFromParams", () => {
  it("converts comma-separated list representation from filter params into a filter value", () => {
    const params = new URLSearchParams();
    params.set("owners", "foo,bar");
    params.set("application", "baz,quux");
    expect(getFilterValueFromParams(params)).toEqual(MOCK_FILTER_VALUE);
  });
});

describe("updateParamsFromFilterValue", () => {
  it("sets filter params to comma-separated list representations of filter values", () => {
    const params = new URLSearchParams();
    const updateSearchParams = jest.fn((cb) => cb(params));
    updateParamsFromFilterValue(updateSearchParams, MOCK_FILTER_VALUE);
    expect(params.get("owners")).toEqual("foo,bar");
    expect(params.get("application")).toEqual("baz,quux");
  });

  it("handles a roundtrip encoding with everything filtered", () => {
    const params = new URLSearchParams();
    const updateSearchParams = jest.fn((cb) => cb(params));
    updateParamsFromFilterValue(updateSearchParams, EVERYTHING_SELECTED_VALUE);
    expect(getFilterValueFromParams(params)).toEqual(EVERYTHING_SELECTED_VALUE);
  });
});

describe("filterExperiments", () => {
  it("filters nothing if filter value is empty", () => {
    expect(filterExperiments(MOCK_EXPERIMENTS, {})).toEqual(MOCK_EXPERIMENTS);
  });

  it("filters only an empty feature config if filter value has everything", () => {
    expect(
      filterExperiments(MOCK_EXPERIMENTS, EVERYTHING_SELECTED_VALUE),
    ).toEqual(MOCK_EXPERIMENTS.filter((e) => e.featureConfig !== null));
  });

  it("filters per individual criteria as expected", () => {
    const names = Object.keys(
      EVERYTHING_SELECTED_VALUE,
    ) as (keyof FilterValue)[];
    for (const name of names) {
      const filterValue = {
        [name]: EVERYTHING_SELECTED_VALUE[name]!.slice(0, 1),
      };
      const result = filterExperiments(MOCK_EXPERIMENTS, filterValue);
      expect(
        result.every((experiment) =>
          filterValue[name].includes(
            experiment![name as keyof getAllExperiments_experiments] as string,
          ),
        ),
      );
    }
  });
});
