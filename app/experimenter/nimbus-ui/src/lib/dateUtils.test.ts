/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  addDaysToDate,
  getProposedEndDate,
  getProposedEnrollmentRange,
} from "./dateUtils";
import { mockSingleDirectoryExperiment as expFactory } from "./mocks";

const FAKE_DATE = "Thu Dec 12 2020";

describe("addDaysToDate", () => {
  it("should add days to a date and return a date string", () => {
    expect(addDaysToDate(FAKE_DATE, 2)).toEqual("Mon Dec 14 2020");
  });
});

describe("addDaysToDate", () => {
  it("should add days to a date and return a date string", () => {
    expect(addDaysToDate(FAKE_DATE, 2)).toEqual("Mon Dec 14 2020");
  });
});

describe("getProposedEndDate", () => {
  it("should return null if no proposedDuration is set", () => {
    const actual = getProposedEndDate(expFactory({ proposedDuration: null }));
    expect(actual).toBeNull();
  });
  it("should render a proposed end date if startDate and proposedDuration are set", () => {
    const actual = getProposedEndDate(
      expFactory({
        startDate: FAKE_DATE,
        proposedDuration: 2,
      }),
    );
    expect(actual).toBe("Dec 14");
  });
  it("should render a duration if no startDate is set", () => {
    const actual = getProposedEndDate(
      expFactory({
        startDate: null,
        proposedDuration: 4,
      }),
    );
    expect(actual).toBe("4 days");
  });
  it("should render '1 day' (not plural) for duration = 1", () => {
    const actual = getProposedEndDate(
      expFactory({
        startDate: null,
        proposedDuration: 1,
      }),
    );
    expect(actual).toBe("1 day");
  });
});

describe("getProposedEnrollmentRange", () => {
  it("should return null if no proposedEnrollment is set", () => {
    const actual = getProposedEnrollmentRange(
      expFactory({ proposedEnrollment: null }),
    );
    expect(actual).toBeNull();
  });
  it("should render a date range if startDate and proposedEnrollment are set", () => {
    const actual = getProposedEnrollmentRange(
      expFactory({
        startDate: FAKE_DATE,
        proposedEnrollment: 4,
      }),
    );
    expect(actual).toBe("Dec 12 to Dec 16");
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
