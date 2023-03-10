/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useConfig } from "src/hooks/useConfig";
import { OutcomesList, OutcomeSlugs } from "src/lib/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export function useOutcomes(experiment: getExperiment_experimentBySlug): {
  primaryOutcomes: OutcomesList;
  secondaryOutcomes: OutcomesList;
  available: OutcomesList;
} {
  const { outcomes } = useConfig();

  const pairOutcomes = (slugs: OutcomeSlugs) => {
    if (!slugs || !outcomes) {
      return [];
    }

    return slugs
      .map((slug) => outcomes!.find((outcome) => outcome!.slug === slug))
      .filter((outcome) => outcome != null);
  };

  const available =
    outcomes?.filter(
      (outcome) => outcome?.application === experiment.application,
    ) || [];

  return {
    primaryOutcomes: pairOutcomes(experiment.primaryOutcomes),
    secondaryOutcomes: pairOutcomes(experiment.secondaryOutcomes),
    available,
  };
}
