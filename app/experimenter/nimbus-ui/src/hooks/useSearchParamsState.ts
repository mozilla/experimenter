/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useLocation, useNavigate } from "@reach/router";
import { useMemo } from "react";

export function useSearchParamsState() {
  const location = useLocation();
  const navigate = useNavigate();
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
