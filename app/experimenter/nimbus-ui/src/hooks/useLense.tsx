/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { createContext, useCallback, useState } from "react";

export enum LenseType {
  Stakeholder = "stakeholder",
  Engineer = "engineer",
}

export const LenseContext = createContext<{
  isEngineer: boolean;
  isStakeholder: boolean;
  setLense: (newLense: LenseType) => void;
}>({ isEngineer: false, isStakeholder: false, setLense: () => {} });

export const useLense = () => {
  const storageKey = "view-lense";
  const storedDefault = localStorage.getItem(
    storageKey,
  ) as keyof typeof LenseType;

  const [lense, setLense] = useState<LenseType>(
    (storedDefault as LenseType) || LenseType.Engineer,
  );

  const setLenseFn = useCallback(
    (newLense: LenseType) => {
      setLense(newLense);
      localStorage.setItem(storageKey, newLense);
    },
    [setLense],
  );

  const lenseContextValues = useCallback(
    () => ({
      isEngineer: lense === LenseType.Engineer,
      isStakeholder: lense === LenseType.Stakeholder,
      setLense: setLenseFn,
    }),
    [lense, setLenseFn],
  );

  return {
    lenseContextValues,
  };
};
