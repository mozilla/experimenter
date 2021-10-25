/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloClient, InMemoryCache } from "@apollo/client/core";
import { cache, cacheConfig, createApolloClient } from "./apollo";

describe("services/apollo", () => {
  describe("cacheConfig", () => {
    const branchFields = cacheConfig.typePolicies!.NimbusBranchType.fields!;

    it("treats a null branch id as undefined", () => {
      // Blur the type here, because we're just concerned with the behavior
      const idField = branchFields.id as (x: any) => any;
      expect(idField(123)).toEqual(123);
      expect(idField(null)).toEqual(undefined);
    });
  });

  describe("cache", () => {
    it("returns an instance of InMemoryCache", () => {
      expect(cache).toBeInstanceOf(InMemoryCache);
    });
  });

  describe("createApolloClient", () => {
    it("returns an instance of ApolloClient", () => {
      expect(createApolloClient()).toBeInstanceOf(ApolloClient);
    });
  });
});
