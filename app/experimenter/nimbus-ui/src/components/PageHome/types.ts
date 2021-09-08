/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getConfig_nimbusConfig } from "../../types/getConfig";

export type FilterOptions = Pick<
  getConfig_nimbusConfig,
  "applications" | "featureConfigs" | "firefoxVersions" | "owners"
>;

export const FilterValueKeys = [
  "owners",
  "applications",
  "featureConfigs",
  "firefoxVersions",
] as const;

export type FilterValue = Partial<
  Record<typeof FilterValueKeys[number], string[]>
>;
