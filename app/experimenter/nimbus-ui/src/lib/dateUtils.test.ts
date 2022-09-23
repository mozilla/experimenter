/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  addDaysToDate,
  getProposedEnrollmentRange,
  humanDate,
} from "./dateUtils";
import { mockSingleDirectoryExperiment as expFactory } from "./mocks";

const FAKE_DATE = "Sat Dec 12 2020";
const FAKE_ISO_DATE = "2020-12-25T15:28:01.821657+00:00";

describe("humanDate", () => {
  it("should produce the date, month and year", () => {
    expect(humanDate(FAKE_ISO_DATE)).toEqual("Dec 25, 2020");
  });

  it("normalizes time and timezone", () => {
    expect(humanDate("2021-06-21T10:00:00Z")).toEqual("Jun 21, 2021");
    expect(humanDate("2021-06-21T00:00:00Z")).toEqual("Jun 21, 2021");
    expect(humanDate("2021-06-21")).toEqual("Jun 21, 2021");
  });
});

describe("addDaysToDate", () => {
  it("should add days to a date and return a date string", () => {
    expect(addDaysToDate(FAKE_DATE, 2)).toEqual("Mon Dec 14 2020");
  });
});

describe("getProposedEnrollmentRange", () => {
  it("should render a date range if startDate and proposedEnrollment are set", () => {
    const actual = getProposedEnrollmentRange(
      expFactory({
        startDate: FAKE_DATE,
        proposedEnrollment: 4,
      }),
    );
    expect(actual).toBe("Dec 12, 2020 - Dec 16, 2020");
  });
  it("should render the enrollment duration if no startDate is set", () => {
    const actual = getProposedEnrollmentRange(
      expFactory({
        startDate: null,
        proposedEnrollment: 4,
      }),
    );
    expect(actual).toBe("4 days");
  });
  it("should render '1 day' (not plural) for proposedEnrollment = 1", () => {
    const actual = getProposedEnrollmentRange(
      expFactory({
        startDate: null,
        proposedEnrollment: 1,
      }),
    );
    expect(actual).toBe("1 day");
  });
});
