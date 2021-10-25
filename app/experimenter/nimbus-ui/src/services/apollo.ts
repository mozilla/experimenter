/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  ApolloClient,
  ApolloLink,
  from,
  InMemoryCache,
  InMemoryCacheConfig,
} from "@apollo/client";
import { createUploadLink } from "apollo-upload-client";
import config from "./config";

export const cacheConfig: InMemoryCacheConfig = {
  typePolicies: {
    NimbusExperimentType: {
      fields: {
        referenceBranch: {
          merge: false,
        },
        treatmentBranches: {
          merge: false,
        },
      },
    },
    NimbusBranchType: {
      fields: {
        id(value: number | null) {
          // HACK: Treat an incoming null ID as undefined, which addresses
          // a caching issue with the initial blank control & treatment
          // branches on new experiment creation
          return value === null ? undefined : value;
        },
      },
    },
  },
};

export const cache = new InMemoryCache(cacheConfig);

export function createApolloClient() {
  // HACK: the type coercion here might be a bad idea, but it seems functional?
  // https://github.com/jaydenseric/apollo-upload-client/issues/268#issuecomment-893907474
  const httpLink = createUploadLink({
    uri: config.graphql_url,
  }) as unknown as ApolloLink;

  const apolloClient = new ApolloClient({
    cache,
    link: from([httpLink]),
  });

  return apolloClient;
}
