/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import pluralize from "./pluralize";

export function humanDate(date: string): string {
  return new Date(date).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function addDaysToDate(datestring: string, days: number): string {
  const date = new Date(datestring);
  date.setDate(date.getDate() + days);
  return date.toDateString();
}

/**
 *  Renders an end date based on proposedDuration (e.g. Dec 2),
 *  or a number of days (e.g. "5 days") if startDate is not set.
 */
export function getProposedEndDate(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
): string | null {
  if (!experiment?.proposedDuration) {
    return null;
  }
  const { startDate, proposedDuration } = experiment;
  if (startDate) {
    return humanDate(addDaysToDate(startDate, proposedDuration));
  } else {
    return pluralize(proposedDuration, "day");
  }
}

/**
 *  Renders period of enrollment depend on what's available
 *  If startDate is set, it will return a range of dates
 *      e.g. Dec 2 - Dec 4
 *  If startDate is not set, it will return a number of days
 *      e.g. 2 days
 */
export function getProposedEnrollmentRange(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
): string | null {
  if (!experiment?.proposedEnrollment) {
    return null;
  }
  const { startDate, proposedEnrollment } = experiment;
  if (startDate) {
    return `${humanDate(startDate)} to ${humanDate(
      addDaysToDate(startDate, proposedEnrollment),
    )}`;
  } else {
    return pluralize(proposedEnrollment, "day");
  }
}
