/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments_owner } from "../../types/getAllExperiments";
import { getConfig_nimbusConfig } from "../../types/getConfig";

export type FilterOptions = {
  owners: Array<getAllExperiments_experiments_owner>;
} & Pick<
  getConfig_nimbusConfig,
  "application" | "featureConfig" | "firefoxMinVersion"
>;

export const FilterValueKeys = [
  "owners",
  "application",
  "featureConfig",
  "firefoxMinVersion",
] as const;

export type FilterValue = Partial<
  Record<typeof FilterValueKeys[number], string[]>
>;
