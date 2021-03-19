/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useCallback, useState } from "react";

export const useFakeMutation = (delay = 1000) => {
  const [loading, setLoading] = useState(false);
  const mockMutationCall = useCallback(() => {
    setLoading(true);
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        setLoading(false);
        resolve();
      }, delay);
    });
  }, [setLoading, delay]);

  return [mockMutationCall, { loading }] as const;
};

export default useFakeMutation;
