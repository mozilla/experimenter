/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export function getDefault() {
  return {
    graphql_url: "",
    sentry_dsn: "",
    version: "",
    featureFlags: {},
  };
}

export type Config = ReturnType<typeof getDefault>;

export function readConfig(mountingElement: HTMLElement) {
  const content = mountingElement.dataset.config;
  update(decode(content));
}

export function decode(content?: string) {
  const isDev = process.env.NODE_ENV === "development";

  if (!content) {
    if (isDev) {
      console.warn("Nimbus is missing server config");
    } else {
      throw new Error("Configuration is empty");
    }
  }

  const decoded = decodeURIComponent(content!);

  try {
    return JSON.parse(decoded);
  } catch (error) {
    if (isDev) {
      console.warn("Nimbus server config is invalid");
    } else {
      throw new Error(
        `Invalid configuration ${JSON.stringify(content)}: ${decoded}`,
      );
    }
  }
}

export function reset() {
  const initial = getDefault();

  // This resets any existing default
  // keys back to their original value
  config = Object.assign(config, initial);

  // This removes any foreign keys that
  // may have found there way in
  Object.keys(config).forEach((key) => {
    if (!initial.hasOwnProperty(key)) {
      delete (config as any)[key];
    }
  });
}

export function update(newData: { [key: string]: any }) {
  config = Object.assign(config, newData);
}

let config = getDefault();
export default config;
