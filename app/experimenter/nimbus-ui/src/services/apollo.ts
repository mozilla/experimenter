/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloClient, InMemoryCache, createHttpLink, from } from "@apollo/client";
import config from "./config";

export const cache = new InMemoryCache();

export function createApolloClient() {
  const httpLink = createHttpLink({
    uri: config.graphql_url,
  });

  const apolloClient = new ApolloClient({
    cache,
    link: from([httpLink]),
  });

  return apolloClient;
}
