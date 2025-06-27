/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useLocation, useNavigate } from "@reach/router";
import React, {
  createContext,
  MutableRefObject,
  useContext,
  useEffect,
  useMemo,
  useRef,
} from "react";

export type SearchParamStorage = Record<string, string>;
export type SearchParamsContextState =
  | MutableRefObject<SearchParamStorage>
  | undefined;

export const SearchParamsContext =
  createContext<SearchParamsContextState>(undefined);

export const SearchParamsStateProvider: React.FC = ({ children }) => {
  const storage = useRef<SearchParamStorage>({});
  return (
    <SearchParamsContext.Provider value={storage}>
      {children}
    </SearchParamsContext.Provider>
  );
};

export function useSearchParamsState(storageKey?: string) {
  const storage = useContext(SearchParamsContext);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(
    () => {
      if (!storage?.current || !storageKey) return;
      if (!location.search) {
        const savedParams = storage.current[storageKey];
        if (savedParams) {
          navigate(`${location.pathname}?${savedParams}`, { replace: true });
        }
      }
    },
    // Only run this effect once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useEffect(() => {
    if (!storage?.current || !storageKey) return;
    const params = new URLSearchParams(location.search);
    storage.current[storageKey] = params.toString();
  }, [navigate, storage, storageKey, location.pathname, location.search]);

  return useMemo(() => {
    const params = new URLSearchParams(location.search);
    const setParams = (updaterFn: (params: URLSearchParams) => void) => {
      const nextParams = new URLSearchParams(location.search);
      updaterFn(nextParams);
      navigate(`${location.pathname}?${nextParams.toString()}`);
    };
    return [params, setParams] as const;
  }, [navigate, location.pathname, location.search]);
}

export type UpdateSearchParams = ReturnType<typeof useSearchParamsState>[1];

export default useSearchParamsState;
