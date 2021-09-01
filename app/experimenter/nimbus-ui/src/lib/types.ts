/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { HistorySource } from "@reach/router";
import { getConfig_nimbusConfig_outcomes } from "../types/getConfig";

export type OutcomeSlugs = (string | null)[] | null;
export type Outcome = getConfig_nimbusConfig_outcomes | null | undefined;
export type OutcomesList = Outcome[];

// This roughly represents optional objects from GQL results
export type NullableObject = Record<string, any> | null;
export type NullableObjectArray = NullableObject[];

// HACK: the types don't cover these properties exposed by the mock
// memory history source, but they're useful for tests
export type MemoryHistorySource = HistorySource & {
  history: HistorySource["history"] & {
    entries: { pathname: string; search: string }[];
    index: number;
  };
};
