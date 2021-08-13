/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export function pluralize(count: number, singular: string, plural?: string) {
  const pluralVal = plural ?? `${singular}s`;
  return `${count} ${count === 1 ? singular : pluralVal}`;
}

export const optionalStringBool = (value: string): boolean | null => {
  return value.length ? value === "true" : null;
};

export const optionalBoolString = (
  value: boolean | null | undefined,
): string | null => {
  if (value == null) {
    return null;
  }
  return String(value);
};

// function getKeyByValue(
//   object: { [key: string]: any },
//   value: { [key: string]: any },
// ) {
//   return Object.keys(object).find((key) => object[key] === value);
// }
