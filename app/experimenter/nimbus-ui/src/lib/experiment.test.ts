/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../types/globalTypes";
import {
  applicationSortSelector,
  channelSortSelector,
  computedEndDateSortSelector,
  editCommonRedirects,
  enrollmentSortSelector,
  experimentSortComparator,
  featureConfigNameSortSelector,
  firefoxMaxVersionSortSelector,
  firefoxMinVersionSortSelector,
  getStatus,
  ownerUsernameSortSelector,
  populationPercentSortSelector,
  resultsReadySortSelector,
  selectFromExperiment,
  startDateSortSelector,
} from "./experiment";
import {
  mockDirectoryExperiments,
  mockExperimentQuery,
  mockSingleDirectoryExperiment,
} from "./mocks";

const { experiment } = mockExperimentQuery("boo");

describe("getStatus", () => {
  it("correctly returns available experiment states", () => {
    experiment.status = NimbusExperimentStatusEnum.DRAFT;
    expect(getStatus(experiment).draft).toBeTruthy();

    experiment.status = NimbusExperimentStatusEnum.PREVIEW;
    expect(getStatus(experiment).preview).toBeTruthy();

    experiment.status = NimbusExperimentStatusEnum.LIVE;
    expect(getStatus(experiment).live).toBeTruthy();
    expect(getStatus(experiment).launched).toBeTruthy();

    experiment.status = NimbusExperimentStatusEnum.COMPLETE;
    expect(getStatus(experiment).complete).toBeTruthy();
    expect(getStatus(experiment).launched).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.IDLE;
    expect(getStatus(experiment).idle).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.APPROVED;
    expect(getStatus(experiment).approved).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.REVIEW;
    expect(getStatus(experiment).review).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.WAITING;
    expect(getStatus(experiment).waiting).toBeTruthy();
  });
});

describe("editCommonRedirects", () => {
  const mockedCall = ({
    status,
    publishStatus,
  }: {
    status?: NimbusExperimentStatusEnum;
    publishStatus?: NimbusExperimentPublishStatusEnum;
  }) => {
    const { experiment } = mockExperimentQuery("boo", {
      status,
      publishStatus,
    });
    return editCommonRedirects({ status: getStatus(experiment) });
  };

  it("returns '' (root) if the experiment is in a launched, non-idle, or preview state", () => {
    expect(mockedCall({ status: NimbusExperimentStatusEnum.LIVE })).toEqual("");
    expect(mockedCall({ status: NimbusExperimentStatusEnum.COMPLETE })).toEqual(
      "",
    );
    expect(
      mockedCall({ publishStatus: NimbusExperimentPublishStatusEnum.WAITING }),
    ).toEqual("");
    expect(mockedCall({ status: NimbusExperimentStatusEnum.PREVIEW })).toEqual(
      "",
    );
  });
});

describe("selectFromExperiment", () => {
  const experiment = mockSingleDirectoryExperiment({
    startDate: "2021-06-29T00:00:00Z",
    proposedEnrollment: 8,
  });

  it("returns a property selected by string name", () => {
    expect(selectFromExperiment(experiment, "name")).toEqual(experiment.name);
  });

  it("returns a property selected via function", () => {
    const selectorCases = [
      [featureConfigNameSortSelector, "Picture-in-Picture"],
      [ownerUsernameSortSelector, "example@mozilla.com"],
      [resultsReadySortSelector, "0"],
      [enrollmentSortSelector, "2021-07-07T00:00:00.000Z"],
      [applicationSortSelector, "DESKTOP"],
      [channelSortSelector, "NIGHTLY"],
      [startDateSortSelector, "2021-06-29T00:00:00Z"],
      [computedEndDateSortSelector, experiment.computedEndDate],
      [firefoxMinVersionSortSelector, "FIREFOX_83"],
      [firefoxMaxVersionSortSelector, "FIREFOX_64"],
      [populationPercentSortSelector, "100.0"],
    ] as const;
    selectorCases.forEach(([selectBy, expected]) =>
      expect(selectFromExperiment(experiment, selectBy)).toEqual(expected),
    );

    expect(
      selectFromExperiment(
        { ...experiment, startDate: null },
        enrollmentSortSelector,
      ),
    ).toEqual("8");
    expect(
      selectFromExperiment(
        { ...experiment, resultsReady: true },
        resultsReadySortSelector,
      ),
    ).toEqual("1");
  });
});

describe("experimentSortComparator", () => {
  const experiments = mockDirectoryExperiments().slice(0, 5);

  it("sorts by name ascending as expected", () => {
    const sortedExperiments = [...experiments].sort(
      experimentSortComparator("name", false),
    );
    const names = sortedExperiments.map(({ name }) => name);
    expect(names).toEqual([
      "Aliquam interdum ac lacus at dictum",
      "Consectetur adipiscing elit",
      "Dolor sit amet",
      "Ipsum dolor sit amet",
      "Lorem ipsum dolor sit amet",
    ]);
  });

  it("sorts by name descending as expected", () => {
    const sortedExperiments = [...experiments].sort(
      experimentSortComparator("name", true),
    );
    const names = sortedExperiments.map(({ name }) => name);
    expect(names).toEqual([
      "Lorem ipsum dolor sit amet",
      "Ipsum dolor sit amet",
      "Dolor sit amet",
      "Consectetur adipiscing elit",
      "Aliquam interdum ac lacus at dictum",
    ]);
  });
});
