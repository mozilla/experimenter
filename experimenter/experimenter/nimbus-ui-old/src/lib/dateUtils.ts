/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { pluralize } from "src/lib/utils";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export function humanDate(date: string): string {
  const parsedDate = new Date(date);
  // Dates currently arrive both with and without time and
  // timezone, so reset time to start of day and force GMT
  parsedDate.setUTCMinutes(0);
  parsedDate.setUTCHours(0);
  parsedDate.setUTCSeconds(0);
  parsedDate.setUTCMilliseconds(0);
  const options: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    timeZone: "GMT",
    year: "numeric",
  };

  return parsedDate.toLocaleString("en-US", options);
}

/**
 *  Renders period of enrollment depend on what's available
 *  If startDate is set, it will return a range of dates
 *      e.g. Dec 2, 2011 - Dec 4, 2011
 *  If startDate is not set, it will return a number of days
 *      e.g. 2 days
 */
export function getProposedEnrollmentRange(
  experiment: getExperiment_experimentBySlug | getAllExperiments_experiments,
): string {
  const {
    startDate,
    computedEnrollmentEndDate,
    proposedEnrollment,
    proposedDuration,
    isRollout,
  } = experiment;
  if (!isRollout) {
    if (startDate && computedEnrollmentEndDate) {
      return `${humanDate(startDate)} - ${humanDate(
        computedEnrollmentEndDate,
      )}`;
    } else {
      return pluralize(proposedEnrollment, "day");
    }
  } else {
    return pluralize(proposedDuration, "day");
  }
}
