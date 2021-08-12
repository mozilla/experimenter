/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useLocation, useNavigate } from "@reach/router";
import { useEffect, useMemo } from "react";

export const genStorageKey = (subkey: string) => `searchParamState:${subkey}`;

export function useSearchParamsState(storageSubKey?: string) {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!storageSubKey) return;
    const storage = window.sessionStorage;
    const storageKey = genStorageKey(storageSubKey);
    if (location.search) {
      const params = new URLSearchParams(location.search);
      storage.setItem(storageKey, params.toString());
    } else {
      const savedParams = storage.getItem(storageKey);
      if (savedParams) {
        navigate(`${location.pathname}?${savedParams}`);
      }
    }
  }, [storageSubKey, location.search]);

  return useMemo(() => {
    const params = new URLSearchParams(location.search);
    const setParams = (updaterFn: (params: URLSearchParams) => void) => {
      const nextParams = new URLSearchParams(location.search);
      updaterFn(nextParams);
      navigate(`${location.pathname}?${nextParams.toString()}`);
    };
    return [params, setParams] as const;
  }, [navigate, location.search]);
}

export type UpdateSearchParams = ReturnType<typeof useSearchParamsState>[1];

export default useSearchParamsState;
