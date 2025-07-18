/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloError, ApolloQueryResult } from "@apollo/client";
import React, { ReactElement, useEffect, useState } from "react";
import ApolloErrorAlert from "src/components/ApolloErrorAlert";
import RefetchAlert from "src/components/RefetchAlert";

export const REFETCH_DELAY = 5000;

export const useRefetchOnError = (
  error: ApolloError | undefined,
  refetch: () => Promise<ApolloQueryResult<any>>,
  refetchAlertClass = "",
) => {
  const [hasRefetched, setHasRefetched] = useState<boolean>(false);
  const [ReactEl, setReactEl] = useState<ReactElement>(<></>);
  useEffect(() => {
    if (!error) return;
    if (!hasRefetched) {
      const timeout = setTimeout(() => {
        refetch();
        setHasRefetched(true);
      }, REFETCH_DELAY);
      setReactEl(<RefetchAlert className={refetchAlertClass} />);
      // abort on component unmount (if users navigate before setTimeout completes)
      return () => clearTimeout(timeout);
    }
    setReactEl(<ApolloErrorAlert {...{ error }} />);
  }, [error, hasRefetched, refetchAlertClass, refetch]);

  return ReactEl;
};
