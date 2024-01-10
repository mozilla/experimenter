/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  FilterOptions,
  FilterValue,
  FilterValueKeys,
  filterValueKeys,
  NonNullFilterOption,
  NonNullFilterOptions,
  OptionalString,
} from "src/components/PageHome/types";
import { UpdateSearchParams } from "src/hooks";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";

type OptionIndexKey<K extends FilterValueKeys> = (
  option: NonNullFilterOption<K>,
) => OptionalString;

export const optionIndexKeys: {
  [key in FilterValueKeys]: OptionIndexKey<key>;
} = {
  owners: (option) => option.username,
  applications: (option) => option.value,
  allFeatureConfigs: (option) => `${option.application}:${option.slug}`,
  firefoxVersions: (option) => option.value,
  channels: (option) => option.value,
  types: (option) => option.value,
  projects: (option) => option.name,
  targetingConfigs: (option) => option.value,
  takeaways: (option) => option.value,
  qaStatus: (option) => option.value,
};

type ExperimentFilter<K extends FilterValueKeys> = (
  option: NonNullFilterOption<K>,
  experiment: getAllExperiments_experiments,
) => boolean;

const experimentFilters: { [key in FilterValueKeys]: ExperimentFilter<key> } = {
  owners: (option, experiment) => experiment.owner.username === option.username,
  applications: (option, experiment) => experiment.application === option.value,
  allFeatureConfigs: (option, experiment) => {
    let featureConfigMatch = false;
    if (experiment.featureConfigs?.length) {
      featureConfigMatch =
        experiment.featureConfigs.filter((f) => f?.slug === option.slug)
          .length > 0;
    }

    let applicationMatch = false;
    if (experiment.featureConfigs?.length) {
      applicationMatch =
        experiment.featureConfigs.filter(
          (f) => f?.application === option.application,
        ).length > 0;
    }
    return featureConfigMatch && applicationMatch;
  },
  firefoxVersions: (option, experiment) =>
    experiment.firefoxMinVersion === option.value,
  channels: (option, experiment) => experiment.channel === option.value,
  types: (option, experiment) => {
    return (
      (experiment.isRollout && option.value === "ROLLOUT") ||
      (!experiment.isRollout && option.value === "EXPERIMENT")
    );
  },
  projects: (option, experiment) => {
    let teamProjectsMatch = false;
    if (experiment.projects?.length) {
      teamProjectsMatch =
        experiment.projects.filter((f) => f?.name === option.name).length > 0;
    }
    return teamProjectsMatch;
  },
  targetingConfigs: (option, experiment) => {
    let targetingConfigMatch = false;
    if (experiment.targetingConfig?.length) {
      targetingConfigMatch =
        experiment.targetingConfig.filter((f) => f?.value === option.value)
          .length > 0;
    }
    return targetingConfigMatch;
  },
  takeaways: (option, experiment) => {
    return (
      (experiment.takeawaysQbrLearning && option.value === "QBR_LEARNING") ||
      (experiment.takeawaysMetricGain && option.value === "DAU_GAIN")
    );
  },
  qaStatus: (option, experiment) => experiment.qaStatus === option.value,
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
      case "allFeatureConfigs":
        filterValue[key] = selectFilterOptions<"allFeatureConfigs">(
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
      case "channels":
        filterValue[key] = selectFilterOptions<"channels">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "types":
        filterValue[key] = selectFilterOptions<"types">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "projects":
        filterValue[key] = selectFilterOptions<"projects">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "targetingConfigs":
        filterValue[key] = selectFilterOptions<"targetingConfigs">(
          options[key],
          optionIndexKeys[key],
          values,
        );
        break;
      case "takeaways":
        filterValue[key] = selectFilterOptions<"takeaways">(
          options[key],
          optionIndexKeys[key],
          values as string[],
        );
        break;
      case "qaStatus":
        filterValue[key] = selectFilterOptions<"qaStatus">(
          options[key],
          optionIndexKeys[key],
          values as string[],
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
        case "allFeatureConfigs":
          values = indexFilterOptions<"allFeatureConfigs">(
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
        case "channels":
          values = indexFilterOptions<"channels">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "types":
          values = indexFilterOptions<"types">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "projects":
          values = indexFilterOptions<"projects">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "targetingConfigs":
          values = indexFilterOptions<"targetingConfigs">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "takeaways":
          values = indexFilterOptions<"takeaways">(
            filterValue[key],
            optionIndexKeys[key],
          );
          break;
        case "qaStatus":
          values = indexFilterOptions<"qaStatus">(
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
      case "allFeatureConfigs":
        filteredExperiments = filterExperimentsByOptions<"allFeatureConfigs">(
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
      case "channels":
        filteredExperiments = filterExperimentsByOptions<"channels">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "types":
        filteredExperiments = filterExperimentsByOptions<"types">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "projects":
        filteredExperiments = filterExperimentsByOptions<"projects">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "targetingConfigs":
        filteredExperiments = filterExperimentsByOptions<"targetingConfigs">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "takeaways":
        filteredExperiments = filterExperimentsByOptions<"takeaways">(
          filterState[key],
          experimentFilters[key],
          filteredExperiments,
        );
        break;
      case "qaStatus":
        filteredExperiments = filterExperimentsByOptions<"qaStatus">(
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
