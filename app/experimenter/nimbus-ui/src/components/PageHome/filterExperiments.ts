/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { UpdateSearchParams } from "../../hooks";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import { FilterValue, FilterValueKeys } from "./types";

// TODO: split the ?filters param up into individual params, rather than use JSON?

export function getFilterValueFromParams(params: URLSearchParams): FilterValue {
  const filterValue: FilterValue = {};
  for (const key of FilterValueKeys) {
    const value = params.get(key);
    if (value) {
      filterValue[key] = value.split(",");
    }
  }
  return filterValue;
}

export function updateParamsFromFilterValue(
  updateSearchParams: UpdateSearchParams,
  filterValue: FilterValue,
) {
  updateSearchParams((params) => {
    for (const key of FilterValueKeys) {
      params.delete(key);
      const values = filterValue[key];
      if (typeof values !== "undefined") {
        params.set(key, values.join(","));
      }
    }
  });
}

type FilterSelector = {
  name: keyof FilterValue;
  selector: (e: getAllExperiments_experiments) => string | null | undefined;
};

const FILTER_SELECTORS: FilterSelector[] = [
  { name: "owners", selector: (e) => e.owner.username },
  { name: "application", selector: (e) => e.application },
  { name: "firefoxMinVersion", selector: (e) => e.firefoxMinVersion },
  { name: "featureConfig", selector: (e) => e.featureConfig?.slug },
];

export function filterExperiments(
  experiments: getAllExperiments_experiments[],
  filterState: FilterValue,
) {
  let filteredExperiments = [...experiments];

  for (const { name, selector } of FILTER_SELECTORS) {
    if (!filterState[name]?.length) continue;
    filteredExperiments = filteredExperiments.filter((e) => {
      const value = selector(e);
      return value && filterState[name]!.includes(value);
    });
  }

  return filteredExperiments;
}

export default filterExperiments;
