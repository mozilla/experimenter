/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useLocation } from "@reach/router";
import { useEffect, useRef } from "react";

export const useScrollToLocationHash = () => {
  const { hash } = useLocation();
  const scrolledToHash = useRef<string | undefined>();

  useEffect(() => {
    if (!hash) return;
    if (scrolledToHash.current !== hash) {
      scrolledToHash.current = hash;
      const id = hash.replace("#", "");
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  });
};
