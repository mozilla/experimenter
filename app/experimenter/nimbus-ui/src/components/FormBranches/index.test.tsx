/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MOCK_CONFIG } from "../../lib/mocks";
import {
  SubjectBranches,
  MOCK_EXPERIMENT,
  MOCK_BRANCH,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
} from "./mocks";

describe("FormBranches", () => {
  it("renders as expected", async () => {
    render(<SubjectBranches />);
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    const branches = screen.queryAllByTestId("FormBranch");
    expect(branches.length).toEqual(
      MOCK_EXPERIMENT!.treatmentBranches!.length + 1,
    );
  });

  it("calls onSave with current state when save button clicked", () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(screen.getByTestId("save-button"));
    expect(onSave).toHaveBeenCalledWith({
      featureConfig: null,
      referenceBranch: MOCK_EXPERIMENT.referenceBranch,
      treatmentBranches: MOCK_EXPERIMENT.treatmentBranches,
    });
  });

  it("calls onNext when next button clicked", () => {
    const onNext = jest.fn();
    render(<SubjectBranches {...{ onNext }} />);
    fireEvent.click(screen.getByTestId("next-button"));
    expect(onNext).toHaveBeenCalled();
  });

  it("sets all branch ratios to 1 when equal ratio checkbox enabled", () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(screen.getByTestId("equal-ratio-checkbox"));
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.referenceBranch.ratio).toEqual(1);
    for (const branch of saveResult.treatmentBranches) {
      expect(branch.ratio).toEqual(1);
    }
  });

  it("supports adding a control branch", () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: null,
            treatmentBranches: null,
          },
        }}
      />,
    );

    onSave.mockClear();
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResultBefore = onSave.mock.calls[0][0];
    expect(saveResultBefore.referenceBranch).toEqual(null);

    fireEvent.click(screen.getByTestId("add-branch"));

    onSave.mockClear();
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResultAfter = onSave.mock.calls[0][0];
    expect(saveResultAfter.referenceBranch).not.toEqual(null);
  });

  it("supports adding a treatment branch", () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            treatmentBranches: null,
          },
        }}
      />,
    );

    onSave.mockClear();
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResultBefore = onSave.mock.calls[0][0];
    expect(saveResultBefore.treatmentBranches).toEqual(null);

    fireEvent.click(screen.getByTestId("add-branch"));

    onSave.mockClear();
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResultAfter = onSave.mock.calls[0][0];
    expect(saveResultAfter.treatmentBranches).not.toEqual(null);
  });

  it("supports removing a treatment branch", () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    const removeFirst = screen.queryAllByTestId("remove-branch")![0];
    fireEvent.click(removeFirst);
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];
    const expectedDeletedBranch = MOCK_EXPERIMENT.treatmentBranches![0]!;
    expect(
      saveResult.treatmentBranches.findIndex(
        (branch: typeof MOCK_BRANCH) =>
          branch.slug === expectedDeletedBranch.slug,
      ),
    ).toEqual(-1);
  });

  it("supports adding feature config", () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfig: null,
          },
        }}
      />,
    );
    const addButton = screen.queryAllByTestId("feature-config-add")[0];
    fireEvent.click(addButton);
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.featureConfig).toEqual(MOCK_CONFIG.featureConfig![0]);
  });

  it("supports removing feature config", () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfig: MOCK_FEATURE_CONFIG,
          },
        }}
      />,
    );
    const addButton = screen.queryAllByTestId("feature-config-remove")[0];
    fireEvent.click(addButton);
    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.featureConfig).toBeNull();
  });

  it("changing feature on one branch changes for all", () => {
    const onSave = jest.fn();
    const featureIdx = 1;
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfig: MOCK_FEATURE_CONFIG,
          },
        }}
      />,
    );
    const featureConfigSelects = screen.queryAllByTestId(
      "feature-config-select",
    )! as HTMLInputElement[];

    // All selectors should be equal before change.
    for (const select of featureConfigSelects) {
      expect(select.value).toEqual(featureConfigSelects[0].value);
    }
    const oldValue = featureConfigSelects[0].value;

    fireEvent.change(featureConfigSelects[0], {
      target: { value: featureIdx },
    });

    // All selectors should have changed
    for (const select of featureConfigSelects) {
      expect(select.value).toEqual(featureConfigSelects[0].value);
      expect(select.value).not.toEqual(oldValue);
    }
  });

  it("updates save result with edits", () => {
    const onSave = jest.fn();
    const { container } = render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfig: MOCK_FEATURE_CONFIG_WITH_SCHEMA,
          },
        }}
      />,
    );
    const branchIdx = 1;

    const expectedData = {
      name: "example name",
      description: "example description",
      ratio: "42",
      featureValue: "example value",
    };

    for (const id of [`branch-reference`, `branch-${branchIdx}`]) {
      for (const [name, value] of Object.entries(expectedData)) {
        const field = container.querySelector(`#${id}-${name}`);
        expect(field).not.toBeNull();
        fireEvent.change(field!, { target: { value } });
      }
    }

    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult).toEqual({
      featureConfig: MOCK_FEATURE_CONFIG_WITH_SCHEMA,
      referenceBranch: {
        ...MOCK_EXPERIMENT.referenceBranch,
        ...expectedData,
      },
      treatmentBranches: [
        MOCK_EXPERIMENT.treatmentBranches![0],
        {
          ...MOCK_EXPERIMENT.treatmentBranches![1],
          ...expectedData,
        },
      ],
    });
  });
});
