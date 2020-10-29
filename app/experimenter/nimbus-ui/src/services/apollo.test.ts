/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { createApolloClient, cache } from "./apollo";
import { ApolloClient, InMemoryCache } from "@apollo/client/core";

describe("services/apollo", () => {
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
