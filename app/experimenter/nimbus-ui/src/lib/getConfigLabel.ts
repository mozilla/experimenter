/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getConfig_nimbusConfig } from "../types/getConfig";

export type ConfigOptions =
  | getConfig_nimbusConfig["application"]
  | getConfig_nimbusConfig["firefoxMinVersion"]
  | getConfig_nimbusConfig["channel"]
  | getConfig_nimbusConfig["targetingConfigSlug"];

export const getConfigLabel = (
  value: string | null,
  configOptions: ConfigOptions,
) => configOptions?.find((option: any) => option.value === value)?.label;
