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
  allFeatureConfigs: MOCK_CONFIG!.allFeatureConfigs!,
  firefoxVersions: MOCK_CONFIG!.firefoxVersions!,
  channels: MOCK_CONFIG!.channels!,
};

export const DEFAULT_VALUE: FilterValue = {
  owners: [],
  applications: [],
  allFeatureConfigs: [],
  firefoxVersions: [],
  channels: [],
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
