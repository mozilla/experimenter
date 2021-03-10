/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useApolloClient } from "@apollo/client";
import { createContext, useContext } from "react";
import { GET_CONFIG_QUERY } from "../gql/config";
import serverConfig from "../services/config";
import { getConfig } from "../types/getConfig";

export type Config = typeof serverConfig & getConfig["nimbusConfig"];
export type MockConfig = Partial<Config> | undefined;
export const MockConfigContext = createContext<MockConfig>(undefined);

/**
 * Hook to retrieve GraphQL and Server config values.
 *
 * NOTE: This hook is dependent on the initial query to retrieve
 * GraphQL config being performed inside the <App> component. Do
 * not use before this component is rendered.
 *
 * Example:
 *
 * const { channel, outcomes } = useConfig();
 */

export function useConfig(): Config {
  const mockConfig = useContext(MockConfigContext) || {};
  const client = useApolloClient();
  const { nimbusConfig } = client.cache.readQuery<{
    nimbusConfig: getConfig["nimbusConfig"];
  }>({
    query: GET_CONFIG_QUERY,
  })!;

  return { ...nimbusConfig!, ...serverConfig, ...mockConfig };
}
