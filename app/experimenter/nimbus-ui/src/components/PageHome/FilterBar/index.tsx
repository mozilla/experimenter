/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useMemo } from "react";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import Select, { OptionsType, OptionTypeBase } from "react-select";
import { NullableObjectArray } from "../../../lib/types";
import { FilterOptions, FilterValue } from "../types";

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
      <Nav className="w-100">
        <FilterSelect
          fieldLabel="Feature"
          fieldOptions={options.featureConfig!}
          filterValueName="featureConfig"
          optionLabelName="name"
          optionValueName="slug"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Application"
          fieldOptions={options.application!}
          filterValueName="application"
          optionLabelName="label"
          optionValueName="value"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Owner"
          fieldOptions={options.owners!}
          filterValueName="owners"
          optionLabelName="username"
          optionValueName="username"
          {...{ filterValue, onChange }}
        />
        <FilterSelect
          fieldLabel="Version"
          fieldOptions={options.firefoxMinVersion!}
          filterValueName="firefoxMinVersion"
          optionLabelName="label"
          optionValueName="value"
          {...{ filterValue, onChange }}
        />
      </Nav>
    </Navbar>
  );
};

type FilterSelectProps<T extends NullableObjectArray> = {
  filterValue: FilterValue;
  onChange: (value: FilterValue) => void;
  filterValueName: keyof FilterOptions;
  fieldLabel: string;
  fieldOptions: T;
  optionLabelName: keyof NonNullable<T[number]>;
  optionValueName: keyof NonNullable<T[number]>;
};

const FilterSelect = <T extends NullableObjectArray>({
  filterValue,
  onChange,
  filterValueName,
  fieldLabel,
  fieldOptions,
  optionLabelName,
  optionValueName,
}: FilterSelectProps<T>) => {
  const filterOptions = useMemo(
    () =>
      fieldOptions.filter(
        (option): option is NonNullable<T[number]> => option !== null,
      ),
    [fieldOptions],
  );
  const fieldValue = filterValue[filterValueName];
  const selectedOptions = useMemo(
    () =>
      filterOptions.filter(
        (option) =>
          typeof option[optionValueName] === "string" &&
          fieldValue?.includes("" + option[optionValueName]),
      ),
    [fieldValue, filterOptions],
  );

  return (
    <Nav.Item className="m-1 mw-25 text-left flex-basis-0 flex-grow-1 flex-shrink-1">
      <label className="ml-1 mr-1" htmlFor={`filter-${filterValueName}`}>
        {fieldLabel}
      </label>
      <Select
        {...{
          name: `filter-${filterValueName}`,
          inputId: `filter-${filterValueName}`,
          isMulti: true,
          value: selectedOptions,
          getOptionLabel: (item: OptionTypeBase) =>
            item[optionLabelName as string],
          getOptionValue: (item: OptionTypeBase) =>
            item[optionValueName as string],
          options: filterOptions,
          onChange: (fieldValue: OptionsType<OptionTypeBase>) => {
            onChange({
              ...filterValue,
              [filterValueName]: fieldValue.map(
                (item) => item[optionValueName as string],
              ),
            });
          },
        }}
      />
    </Nav.Item>
  );
};

export default FilterBar;
