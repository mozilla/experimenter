/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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
  qaStatusSortSelector,
  resultsReadySortSelector,
  selectFromExperiment,
  startDateSortSelector,
  unpublishedUpdatesSortSelector,
} from "src/lib/experiment";
import {
  mockDirectoryExperiments,
  mockExperimentQuery,
  mockSingleDirectoryExperiment,
} from "src/lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentQAStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

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

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.IDLE;
    experiment.isRolloutDirty = true;
    expect(getStatus(experiment).dirty).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.REVIEW;
    experiment.status = NimbusExperimentStatusEnum.LIVE;
    experiment.statusNext = NimbusExperimentStatusEnum.LIVE;
    experiment.isRollout = true;
    expect(getStatus(experiment).updateRequested).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.APPROVED;
    expect(getStatus(experiment).updateRequestedApproved).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatusEnum.WAITING;
    expect(getStatus(experiment).updateRequestedWaiting).toBeTruthy();
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
      [qaStatusSortSelector, NimbusExperimentQAStatusEnum.GREEN],
      [enrollmentSortSelector, "2021-07-07T00:00:00.000Z"],
      [applicationSortSelector, "DESKTOP"],
      [channelSortSelector, "NIGHTLY"],
      [startDateSortSelector, "2021-06-29T00:00:00Z"],
      [computedEndDateSortSelector, experiment.computedEndDate],
      [firefoxMinVersionSortSelector, "FIREFOX_83"],
      [firefoxMaxVersionSortSelector, "FIREFOX_64"],
      [populationPercentSortSelector, "100"],
      [unpublishedUpdatesSortSelector, "0"],
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
        {
          ...experiment,
          publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
        },
        unpublishedUpdatesSortSelector,
      ),
    ).toEqual("0");
    expect(
      selectFromExperiment(
        { ...experiment, resultsReady: true },
        resultsReadySortSelector,
      ),
    ).toEqual("1");
  });

  it("returns nothing for qa status not set", () => {
    const experiment = mockSingleDirectoryExperiment({
      qaStatus: null,
    });
    expect(
      selectFromExperiment(
        { ...experiment, qaStatus: null },
        qaStatusSortSelector,
      ),
    ).toEqual("0");
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
