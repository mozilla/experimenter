/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { formBranchesReducer, FormBranchesState } from "./reducer";
import { MOCK_EXPERIMENT } from "./mocks";

const MOCK_STATE: FormBranchesState = {
  equalRatio: true,
  lastId: 0,
  featureConfig: MOCK_EXPERIMENT.featureConfig,
  referenceBranch: {
    __key: "branch-reference",
    ...MOCK_EXPERIMENT.referenceBranch!,
  },
  treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch, idx) => ({
    ...branch!,
    __key: `branch-${idx}`,
  })),
};

describe("formBranchesReducer", () => {
  // Most code paths in reducer are exercised in UI tests - these tests
  // catch a few corner cases for the sake of coverage.

  it("yields the same state on an unknown action", () => {
    const oldState = { ...MOCK_STATE };
    const newState = formBranchesReducer(
      oldState,
      //@ts-ignore intentionally breaking the type to exercise default case
      { type: "bogusAction" },
    );
    expect(newState).toEqual(oldState);
  });

  it("addBranch creates a new referenceBranch as necessary", () => {
    const oldState = {
      ...MOCK_STATE,
      referenceBranch: null,
      treatmentBranches: null,
    };
    const newState = formBranchesReducer(oldState, { type: "addBranch" });
    expect(newState.referenceBranch).not.toBeNull();
  });

  it("addBranch creates a new treatmentBranches array as necessary", () => {
    const oldState = {
      ...MOCK_STATE,
      treatmentBranches: null,
    };
    const newState = formBranchesReducer(oldState, { type: "addBranch" });
    expect(Array.isArray(newState.treatmentBranches)).toEqual(true);
  });

  it("addBranch pushes onto existing treatmentBranches array", () => {
    const oldState = {
      ...MOCK_STATE,
      treatmentBranches: [],
    };
    const newState = formBranchesReducer(oldState, { type: "addBranch" });
    expect(newState.treatmentBranches!.length).toEqual(1);
  });

  it("equalRatio does nothing to branches if setting to false", () => {
    const oldState = {
      ...MOCK_STATE,
      referenceBranch: null,
      treatmentBranches: null,
    };
    const newState = formBranchesReducer(oldState, {
      type: "setEqualRatio",
      value: false,
    });
    expect(newState).toEqual({ ...oldState, equalRatio: false });
  });

  it("equalRatio set to true skips null branches", () => {
    const oldState = {
      ...MOCK_STATE,
      equalRatio: false,
      referenceBranch: null,
      treatmentBranches: null,
    };
    const newState = formBranchesReducer(oldState, {
      type: "setEqualRatio",
      value: true,
    });
    expect(newState).toEqual({ ...oldState, equalRatio: true });
  });
});
