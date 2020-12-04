/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useAsync } from "react-async-hook";
import { AnalysisData } from "../lib/visualization/types";

export const fetchData = async (slug: string) =>
  (
    await fetch(`/api/v3/visualization/${encodeURIComponent(slug)}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
  ).json();

/**
 * Hook to retrieve Experiment Analysis data by slug.
 */

export function useAnalysis() {
  // Because this is delayed execution the returned `execute`
  // function needs to provide the slug parameter
  return useAsync<AnalysisData>(fetchData, [], {
    executeOnMount: false,
    executeOnUpdate: false,
  });
}
