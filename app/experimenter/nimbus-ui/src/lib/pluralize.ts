/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export default function pluralize(
  count: number,
  singular: string,
  plural?: string,
) {
  const pluralVal = plural ?? `${singular}s`;
  return `${count} ${count === 1 ? singular : pluralVal}`;
}
