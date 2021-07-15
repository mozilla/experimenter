/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../types/globalTypes";
import { editCommonRedirects, getStatus } from "./experiment";
import { mockExperimentQuery } from "./mocks";

const { experiment } = mockExperimentQuery("boo");

describe("getStatus", () => {
  it("correctly returns available experiment states", () => {
    experiment.status = NimbusExperimentStatus.DRAFT;
    expect(getStatus(experiment).draft).toBeTruthy();

    experiment.status = NimbusExperimentStatus.PREVIEW;
    expect(getStatus(experiment).preview).toBeTruthy();

    experiment.status = NimbusExperimentStatus.LIVE;
    expect(getStatus(experiment).live).toBeTruthy();
    expect(getStatus(experiment).launched).toBeTruthy();

    experiment.status = NimbusExperimentStatus.COMPLETE;
    expect(getStatus(experiment).complete).toBeTruthy();
    expect(getStatus(experiment).launched).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatus.IDLE;
    expect(getStatus(experiment).idle).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatus.APPROVED;
    expect(getStatus(experiment).approved).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatus.REVIEW;
    expect(getStatus(experiment).review).toBeTruthy();

    experiment.publishStatus = NimbusExperimentPublishStatus.WAITING;
    expect(getStatus(experiment).waiting).toBeTruthy();
  });
});

describe("editCommonRedirects", () => {
  const mockedCall = ({
    status,
    publishStatus,
  }: {
    status?: NimbusExperimentStatus;
    publishStatus?: NimbusExperimentPublishStatus;
  }) => {
    const { experiment } = mockExperimentQuery("boo", {
      status,
      publishStatus,
    });
    return editCommonRedirects({ status: getStatus(experiment) });
  };

  it("returns '' (root) if the experiment is in a launched, non-idle, or preview state", () => {
    expect(mockedCall({ status: NimbusExperimentStatus.LIVE })).toEqual("");
    expect(mockedCall({ status: NimbusExperimentStatus.COMPLETE })).toEqual("");
    expect(
      mockedCall({ publishStatus: NimbusExperimentPublishStatus.WAITING }),
    ).toEqual("");
    expect(mockedCall({ status: NimbusExperimentStatus.PREVIEW })).toEqual("");
  });
});
