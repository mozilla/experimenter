/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { pluralize } from "./utils";

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

export function addDaysToDate(datestring: string, days: number): string {
  const date = new Date(datestring);
  date.setDate(date.getDate() + days);
  return date.toDateString();
}

/**
 *  Renders period of enrollment depend on what's available
 *  If startDate is set, it will return a range of dates
 *      e.g. Dec 2 - Dec 4
 *  If startDate is not set, it will return a number of days
 *      e.g. 2 days
 */
export function getProposedEnrollmentRange(
  experiment: getExperiment_experimentBySlug | getAllExperiments_experiments,
): string {
  const { startDate, proposedEnrollment } = experiment;
  if (startDate) {
    return `${humanDate(startDate)} to ${humanDate(
      addDaysToDate(startDate, proposedEnrollment),
    )}`;
  } else {
    return pluralize(proposedEnrollment, "day");
  }
}
