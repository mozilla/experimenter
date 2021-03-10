/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { OutcomesList, OutcomeSlugs } from "../lib/types";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { useConfig } from "./useConfig";

export function useOutcomes(
  experiment: getExperiment_experimentBySlug,
): { primaryOutcomes: OutcomesList; secondaryOutcomes: OutcomesList } {
  const { outcomes } = useConfig();

  const pairOutcomes = (slugs: OutcomeSlugs) => {
    if (!slugs || !outcomes) {
      return [];
    }

    return slugs
      .map((slug) => outcomes!.find((outcome) => outcome!.slug === slug))
      .filter((outcome) => outcome != null);
  };

  return {
    primaryOutcomes: pairOutcomes(experiment.primaryOutcomes),
    secondaryOutcomes: pairOutcomes(experiment.secondaryOutcomes),
  };
}
