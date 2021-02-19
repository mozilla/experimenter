/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { NimbusExperimentStatus } from "../types/globalTypes";
import { editCommonRedirects, getStatus } from "./experiment";
import { mockExperimentQuery } from "./mocks";

const { experiment } = mockExperimentQuery("boo");

describe("getStatus", () => {
  it("correctly returns available experiment states", () => {
    experiment.status = NimbusExperimentStatus.DRAFT;
    expect(getStatus(experiment).draft).toBeTruthy();

    experiment.status = NimbusExperimentStatus.REVIEW;
    expect(getStatus(experiment).review).toBeTruthy();

    experiment.status = NimbusExperimentStatus.ACCEPTED;
    expect(getStatus(experiment).accepted).toBeTruthy();
    expect(getStatus(experiment).locked).toBeTruthy();

    experiment.status = NimbusExperimentStatus.PREVIEW;
    expect(getStatus(experiment).preview).toBeTruthy();
    expect(getStatus(experiment).locked).toBeTruthy();

    experiment.status = NimbusExperimentStatus.LIVE;
    expect(getStatus(experiment).live).toBeTruthy();
    expect(getStatus(experiment).released).toBeTruthy();
    expect(getStatus(experiment).locked).toBeTruthy();

    experiment.status = NimbusExperimentStatus.COMPLETE;
    expect(getStatus(experiment).complete).toBeTruthy();
    expect(getStatus(experiment).released).toBeTruthy();
    expect(getStatus(experiment).locked).toBeTruthy();
  });
});

describe("editCommonRedirects", () => {
  const mockedCall = (status: NimbusExperimentStatus) => {
    const { experiment } = mockExperimentQuery("boo", { status });
    return editCommonRedirects({ status: getStatus(experiment) });
  };

  it("returns 'request-review' if the experiment is in review or preview", () => {
    expect(mockedCall(NimbusExperimentStatus.REVIEW)).toEqual("request-review");
    // @ts-ignore until backend API & types are updated
    expect(mockedCall("PREVIEW")).toEqual("request-review");
  });

  it("returns 'design' if the experiment is in a locked state", () => {
    expect(mockedCall(NimbusExperimentStatus.LIVE)).toEqual("design");
    expect(mockedCall(NimbusExperimentStatus.COMPLETE)).toEqual("design");
    expect(mockedCall(NimbusExperimentStatus.ACCEPTED)).toEqual("design");
  });
});
