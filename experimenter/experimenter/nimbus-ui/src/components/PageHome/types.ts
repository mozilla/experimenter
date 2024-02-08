/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getConfig_nimbusConfig } from "src/types/getConfig";

export const filterValueKeys = [
  "owners",
  "applications",
  "allFeatureConfigs",
  "firefoxVersions",
  "channels",
  "types",
  "projects",
  "targetingConfigs",
  "takeaways",
  "qaStatus",
] as const;

export type FilterValueKeys = typeof filterValueKeys[number];

export type FilterOptions = Pick<getConfig_nimbusConfig, FilterValueKeys>;

export type FilterValue = Partial<FilterOptions>;

export type OptionalString = string | null | undefined;

// Very awkward type representing a property of FilterOptions that has been
// verified as not null. Typescript does not infer this, for some reason.
export type NonNullFilterOptions<K extends FilterValueKeys> = NonNullable<
  FilterOptions[K]
>[number][];

export type NonNullFilterOption<K extends FilterValueKeys> = NonNullable<
  NonNullFilterOptions<K>[number]
>;
