/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useMemo } from "react";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Select, { OptionsType, OptionTypeBase } from "react-select";
import { optionIndexKeys } from "../filterExperiments";
import {
  FilterOptions,
  FilterValue,
  FilterValueKeys,
  NonNullFilterOption,
  NonNullFilterOptions,
} from "../types";

export type FilterBarProps = {
  options: FilterOptions;
  value: FilterValue;
  onChange: (value: FilterValue) => void;
};

export const FilterBar: React.FC<FilterBarProps> = ({
  options,
  value: filterValue,
  onChange,
}) => {
  return (
    <Navbar variant="light" bg="light" className="nav-fill mt-4 mb-4">
      <Nav className="w-100 flex-column">
        <h5 className="ml-1">{"Filters"}</h5>
        <FilterSelect
          fieldLabel="Feature"
          fieldOptions={options.allFeatureConfigs!}
          filterValueName="allFeatureConfigs"
          optionLabelName="name"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Application"
          fieldOptions={options.applications!}
          filterValueName="applications"
          optionLabelName="label"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Owner"
          fieldOptions={options.owners!}
          filterValueName="owners"
          optionLabelName="username"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Version"
          fieldOptions={options.firefoxVersions!}
          filterValueName="firefoxVersions"
          optionLabelName="label"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Channel"
          fieldOptions={options.channels!}
          filterValueName="channels"
          optionLabelName="label"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Type"
          fieldOptions={options.types!}
          filterValueName="types"
          optionLabelName="label"
          {...{ filterValue, onChange }}
        />
      </Nav>
    </Navbar>
  );
};

type FilterSelectProps<
  K extends FilterValueKeys,
  T extends NonNullFilterOptions<K>,
> = {
  filterValue: FilterValue;
  onChange: (value: FilterValue) => void;
  filterValueName: K;
  fieldLabel: string;
  fieldOptions: T;
  optionLabelName: keyof NonNullFilterOption<K>;
};

const FilterSelect = <
  K extends FilterValueKeys,
  T extends NonNullFilterOptions<K>,
>({
  filterValue,
  onChange,
  filterValueName,
  fieldLabel,
  fieldOptions,
  optionLabelName,
}: FilterSelectProps<K, T>) => {
  const filterOptions = useMemo(
    () =>
      (fieldOptions! as NonNullFilterOptions<K>).filter(
        (option): option is NonNullable<typeof option> => !!option,
      ),
    [fieldOptions],
  );
  const fieldValue = filterValue[filterValueName];

  return (
    <Nav.Item className="m-1 text-left flex-basis-0 flex-grow-1 flex-shrink-1 w-100">
      <Select
        {...{
          name: `filter-${filterValueName}`,
          inputId: `filter-${filterValueName}`,
          isMulti: true,
          value: fieldValue,
          placeholder: "All " + fieldLabel + "s",
          getOptionLabel: (item: OptionTypeBase) =>
            item[optionLabelName as string],
          getOptionValue: (item: OptionTypeBase) =>
            optionIndexKeys[filterValueName](
              // @ts-ignore because this works in practice but types disagree
              item as NonNullFilterOption<K>,
            )!,
          options: filterOptions,
          onChange: (fieldValue: OptionsType<OptionTypeBase>) => {
            onChange({
              ...filterValue,
              [filterValueName]: fieldValue,
            });
          },
        }}
      />
    </Nav.Item>
  );
};

export default FilterBar;
