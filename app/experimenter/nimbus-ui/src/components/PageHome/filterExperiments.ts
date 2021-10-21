/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { UpdateSearchParams } from "../../hooks";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import {
  FilterOptions,
  FilterValue,
  FilterValueKeys,
  filterValueKeys,
  NonNullFilterOption,
  NonNullFilterOptions,
  OptionalString,
} from "./types";

type OptionIndexKey<K extends FilterValueKeys> = (
  option: NonNullFilterOption<K>,
) => OptionalString;

const optionIndexKeys: { [key in FilterValueKeys]: OptionIndexKey<key> } = {
  owners: (option) => option.username,
  applications: (option) => option.value,
  featureConfigs: (option) => `${option.application}:${option.slug}`,
  firefoxVersions: (option) => option.value,
};

type ExperimentFilter<K extends FilterValueKeys> = (
  option: NonNullFilterOption<K>,
  experiment: getAllExperiments_experiments,
) => boolean;

const experimentFilters: { [key in FilterValueKeys]: ExperimentFilter<key> } = {
  owners: (option, experiment) => experiment.owner.username === option.username,
  applications: (option, experiment) => experiment.application === option.value,
  featureConfigs: (option, experiment) =>
    experiment.featureConfig?.slug === option.slug &&
    experiment.featureConfig?.application === option.application,
  firefoxVersions: (option, experiment) =>
    experiment.firefoxMinVersion === option.value,
};

export function getFilterValueFromParams(
  options: FilterOptions,
  params: URLSearchParams,
): FilterValue {
  const filterValue: FilterValue = {};
  for (const key of filterValueKeys) {
    const values = params.get(key)?.split(",");
    if (!values) continue;
    // Verbose switch that seems to make types happier
    switch (key) {
      case "owners":
        filterValue[key] = selectFilterOptions<"owners">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "applications":
        filterValue[key] = selectFilterOptions<"applications">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "featureConfigs":
        filterValue[key] = selectFilterOptions<"featureConfigs">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "firefoxVersions":
        filterValue[key] = selectFilterOptions<"firefoxVersions">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
    }
  }
  return filterValue;
}

function selectFilterOptions<K extends FilterValueKeys>(
  fieldOptions: FilterOptions[K],
  optionKey: OptionIndexKey<K>,
  values: string[],
) {
  if (!fieldOptions) return [];
  return (fieldOptions as NonNullFilterOptions<K>).filter((option) => {
    if (option === null) return false;
    const key = optionKey(option as NonNullable<typeof option>);
    if (!key) return false;
    return values.includes(key);
  });
}

export function updateParamsFromFilterValue(
  updateSearchParams: UpdateSearchParams,
  filterValue: FilterValue,
) {
  updateSearchParams((params) => {
    for (const key of filterValueKeys) {
      params.delete(key);
      let values;
      // Verbose switch that seems to make types happier
      switch (key) {
        case "owners":
          values = indexFilterOptions<"owners">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "applications":
          values = indexFilterOptions<"applications">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "featureConfigs":
          values = indexFilterOptions<"featureConfigs">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "firefoxVersions":
          values = indexFilterOptions<"firefoxVersions">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
      }
      if (values && values.length) {
        params.set(key, values.join(","));
      }
    }
  });
}

function indexFilterOptions<K extends FilterValueKeys>(
  selectedOptions: FilterOptions[K] | undefined,
  optionKey: OptionIndexKey<K>,
) {
  if (!selectedOptions) return;
  return (selectedOptions as NonNullFilterOptions<K>)
    .filter((option): option is NonNullable<typeof option> => !!option)
    .map(optionKey);
}

export function filterExperiments(
  experiments: getAllExperiments_experiments[],
  filterState: FilterValue,
) {
  let filteredExperiments = [...experiments];
  for (const key of filterValueKeys) {
    // Verbose switch that seems to make types happier
    switch (key) {
      case "owners":
        filteredExperiments = filterExperimentsByOptions<"owners">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "applications":
        filteredExperiments = filterExperimentsByOptions<"applications">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "featureConfigs":
        filteredExperiments = filterExperimentsByOptions<"featureConfigs">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "firefoxVersions":
        filteredExperiments = filterExperimentsByOptions<"firefoxVersions">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
    }
  }
  return filteredExperiments;
}

function filterExperimentsByOptions<K extends FilterValueKeys>(
  selectedOptions: FilterOptions[K] | undefined,
  experimentFilter: ExperimentFilter<K>,
  experiments: getAllExperiments_experiments[],
) {
  return experiments.filter((experiment) => {
    if (!selectedOptions) return true;
    return (selectedOptions as NonNullFilterOptions<K>)
      .filter((option): option is NonNullable<typeof option> => !!option)
      .some((option) => experimentFilter(option, experiment));
  });
}

export default filterExperiments;
