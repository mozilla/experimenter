/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { FilterBar, FilterSelect } from "src/components/PageHome/FilterBar";
import { FilterOptions, FilterValue } from "src/components/PageHome/types";
import { mockDirectoryExperiments, MOCK_CONFIG } from "src/lib/mocks";

export const MOCK_EXPERIMENTS = mockDirectoryExperiments();

export const DEFAULT_OPTIONS: FilterOptions = {
  owners: MOCK_CONFIG!.owners,
  applications: MOCK_CONFIG!.applications!,
  allFeatureConfigs: MOCK_CONFIG!.allFeatureConfigs!,
  firefoxVersions: MOCK_CONFIG!.firefoxVersions!,
  channels: MOCK_CONFIG!.channels!,
  takeaways: MOCK_CONFIG!.takeaways,
  types: MOCK_CONFIG!.types,
  projects: MOCK_CONFIG!.projects!,
  targetingConfigs: MOCK_CONFIG!.targetingConfigs,
  qaStatus: MOCK_CONFIG!.qaStatus,
};

export const DEFAULT_VALUE: FilterValue = {
  owners: [],
  applications: [],
  allFeatureConfigs: [],
  firefoxVersions: [],
  channels: [],
  takeaways: [],
  types: [],
  projects: [],
  targetingConfigs: [],
  qaStatus: [],
};

export const EVERYTHING_SELECTED_VALUE: FilterValue = DEFAULT_OPTIONS;

export const Subject = ({
  options = DEFAULT_OPTIONS,
  value = DEFAULT_VALUE,
}: Partial<React.ComponentProps<typeof FilterBar>>) => {
  const [filterState, setFilterState] = useState<FilterValue>(value);
  const onChange = (newState: FilterValue) => setFilterState(newState);
  return (
    <div>
      <FilterBar {...{ options, value: filterState, onChange }} />
      <div>
        <h3>Filter state</h3>
        <pre>{JSON.stringify(filterState, null, "  ")}</pre>
      </div>
    </div>
  );
};

export const FilterSelectSubject = ({
  filterValue = DEFAULT_VALUE,
  onChange = () => {},
  filterValueName,
  fieldLabel,
  fieldOptions,
}: Partial<React.ComponentProps<typeof FilterSelect>>) => {
  return (
    <FilterSelect
      filterValueName={filterValueName!}
      fieldLabel={fieldLabel!}
      fieldOptions={fieldOptions!}
      {...{ filterValue, onChange }}
    />
  );
};
