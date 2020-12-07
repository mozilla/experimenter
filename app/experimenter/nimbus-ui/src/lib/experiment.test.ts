/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { NimbusExperimentStatus } from "../types/globalTypes";
import { getStatus } from "./experiment";
import { mockExperimentQuery } from "./mocks";

const experiment = mockExperimentQuery("boo").data!;

describe("getStatus", () => {
  it("correctly returns available experiment states", () => {
    experiment.status = NimbusExperimentStatus.DRAFT;
    expect(getStatus(experiment).draft).toBeTruthy();

    experiment.status = NimbusExperimentStatus.REVIEW;
    expect(getStatus(experiment).review).toBeTruthy();

    experiment.status = NimbusExperimentStatus.ACCEPTED;
    expect(getStatus(experiment).accepted).toBeTruthy();
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
