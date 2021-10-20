/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { mockDirectoryExperiments, MOCK_CONFIG } from "../../lib/mocks";
import { FilterBar } from "./FilterBar";
import { FilterOptions, FilterValue } from "./types";

export const MOCK_EXPERIMENTS = mockDirectoryExperiments();

export const DEFAULT_OPTIONS: FilterOptions = {
  owners: MOCK_CONFIG!.owners,
  applications: MOCK_CONFIG!.applications!,
  featureConfigs: MOCK_CONFIG!.featureConfigs!,
  firefoxVersions: MOCK_CONFIG!.firefoxVersions!,
};

export const DEFAULT_VALUE: FilterValue = {
  owners: [],
  applications: [],
  featureConfigs: [],
  firefoxVersions: [],
};

export const EVERYTHING_SELECTED_VALUE: FilterValue = {
  owners: MOCK_CONFIG!.owners!.map((a) => a!.username!),
  applications: MOCK_CONFIG!.applications!.map((a) => a!.value!),
  firefoxVersions: MOCK_CONFIG!.firefoxVersions!.map((a) => a!.value!),
  featureConfigs: MOCK_CONFIG!.featureConfigs!.map((a) => a!.slug!),
};

export const Subject = ({
  options = DEFAULT_OPTIONS,
  value = DEFAULT_VALUE,
  onChange = () => {},
}: Partial<React.ComponentProps<typeof FilterBar>>) => {
  const [filterState, setFilterState] = useState<FilterValue>(value);
  const onChangeWithState = (newState: FilterValue) => {
    setFilterState(newState);
    onChange(newState);
  };
  return (
    <div>
      <FilterBar
        {...{ options, value: filterState, onChange: onChangeWithState }}
      />
      <div>
        <h3>Filter state</h3>
        <pre>{JSON.stringify(filterState, null, "  ")}</pre>
      </div>
    </div>
  );
};
