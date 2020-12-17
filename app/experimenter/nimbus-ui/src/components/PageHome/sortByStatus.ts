/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getStatus } from "../../lib/experiment";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";

export type ExperimentCollector = Record<
  "draft" | "review" | "live" | "complete",
  getAllExperiments_experiments[]
>;

function sortByStatus(experiments: getAllExperiments_experiments[] = []) {
  return experiments.reduce<ExperimentCollector>(
    (collector, experiment) => {
      const status = getStatus(experiment);
      if (status.live) {
        collector.live.push(experiment);
      } else if (status.complete) {
        collector.complete.push(experiment);
      } else if (status.review || status.accepted) {
        collector.review.push(experiment);
      } else {
        collector.draft.push(experiment);
      }
      return collector;
    },
    {
      draft: [],
      review: [],
      live: [],
      complete: [],
    },
  );
}

export default sortByStatus;
