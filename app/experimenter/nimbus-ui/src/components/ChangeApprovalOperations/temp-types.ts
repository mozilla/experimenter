/* istanbul ignore file until EXP-1055 & EXP-1062 done */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// Replace with generated types, EXP-1055 & EXP-1062
export type NimbusUser = {
  email: string | null;
} | null;

export type NimbusChangeLogType = {
  changedOn: DateTime | null;
  changedBy: NimbusUser | null;
  message: string | null;
} | null;
