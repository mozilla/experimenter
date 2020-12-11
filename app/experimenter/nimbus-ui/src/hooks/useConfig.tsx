/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useApolloClient } from "@apollo/client";
import { GET_CONFIG_QUERY } from "../gql/config";
import { getConfig } from "../types/getConfig";
import serverConvig from "../services/config";

/**
 * Hook to retrieve GraphQL and Server config valyes.
 *
 * NOTE: This hook is dependent on the initial query to retrieve
 * GraphQL config being performed inside the <App> component. Do
 * not use before this component is rendered.
 *
 * Example:
 *
 * const { channel, probeSets } = useConfig();
 */

export function useConfig() {
  const client = useApolloClient();
  const { nimbusConfig } = client.cache.readQuery<{
    nimbusConfig: getConfig["nimbusConfig"];
  }>({
    query: GET_CONFIG_QUERY,
  })!;

  return { ...nimbusConfig!, ...serverConvig };
}
