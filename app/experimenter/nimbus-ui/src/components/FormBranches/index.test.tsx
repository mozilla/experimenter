/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  act,
  waitFor,
} from "@testing-library/react";
import { MOCK_CONFIG } from "../../lib/mocks";
import {
  SubjectBranches,
  MOCK_EXPERIMENT,
  MOCK_BRANCH,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
} from "./mocks";
import { extractUpdateBranch } from "./reducer/update";

describe("FormBranches", () => {
  it("renders as expected", async () => {
    render(<SubjectBranches />);
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    const branches = screen.queryAllByTestId("FormBranch");
    expect(branches.length).toEqual(
      MOCK_EXPERIMENT!.treatmentBranches!.length + 1,
    );
  });

  it("renders as expected while loading", async () => {
    const onSave = jest.fn();
    const onNext = jest.fn();
    render(<SubjectBranches {...{ isLoading: true, onSave, onNext }} />);
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("save-button")).toHaveTextContent("Saving");
    fireEvent.click(screen.getByTestId("save-button"));
    expect(onSave).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("next-button"));
    expect(onNext).not.toHaveBeenCalled();
  });

  it("calls onSave with extracted update when save button clicked", () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(screen.getByTestId("save-button"));
    expect(onSave).toHaveBeenCalled();
    const onSaveArgs = onSave.mock.calls[0];
    expect(onSaveArgs[0]).toEqual({
      featureConfigId: null,
      // @ts-ignore type mismatch covers discarded annotation properties
      referenceBranch: extractUpdateBranch(MOCK_EXPERIMENT.referenceBranch!),
      treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map(
        // @ts-ignore type mismatch covers discarded annotation properties
        (branch) => extractUpdateBranch(branch!),
      ),
    });
    expect(typeof onSaveArgs[1]).toEqual("function");
    expect(typeof onSaveArgs[2]).toEqual("function");
  });

  it("displays submit errors set by onSave handler", async () => {
    const expectedErrors = {
      "*": ["Global error alert"],
      reference_branch: {
        name: ["Bad name"],
      },
    };
    const onSave = jest.fn((state, setSubmitErrors /*, clearSubmitErrors*/) => {
      setSubmitErrors(expectedErrors);
    });
    const { container } = render(
      <SubjectBranches {...{ onSave, saveOnInitialRender: true }} />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("global-error")).toHaveTextContent(
        expectedErrors["*"][0],
      );
      expect(
        container.querySelector('*[data-for="branch-reference-name"]'),
      ).toHaveTextContent(expectedErrors["reference_branch"]["name"][0]);
    });
  });

  it("can clear submit errors after set by onSave handler", async () => {
    const expectedErrors = {
      "*": ["Global error alert"],
      reference_branch: {
        name: ["Bad name"],
      },
    };
    const onSave = jest.fn((state, setSubmitErrors, clearSubmitErrors) => {
      setSubmitErrors(expectedErrors);
      clearSubmitErrors();
    });
    const { container } = render(
      <SubjectBranches {...{ onSave, saveOnInitialRender: true }} />,
    );
    expect(screen.queryByTestId("global-error")).not.toBeInTheDocument();
    expect(
      container.querySelector('*[data-for="branch-reference-name"]'),
    ).not.toBeInTheDocument();
  });

  it("displays exception thrown by onSaveHandler", async () => {
    const expectedErrorMessage = "Super bad thing happened";
    const onSave = jest.fn(() => {
      throw new Error(expectedErrorMessage);
    });
    render(<SubjectBranches {...{ onSave, saveOnInitialRender: true }} />);
    await waitFor(() => {
      expect(screen.getByTestId("global-error")).toHaveTextContent(
        expectedErrorMessage,
      );
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

  it("requires adding a valid control branch before save is enabled", async () => {
    const onSave = jest.fn();
    const { container } = render(
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

    expect(screen.getByTestId("save-button")).toBeDisabled();

    fireEvent.click(screen.getByTestId("add-branch"));
    selectFeatureConfig();
    await fillInBranch(container, "branch-reference");
    expect(screen.getByTestId("save-button")).not.toBeDisabled();

    fireEvent.click(screen.getByTestId("save-button"));
    const saveResultAfter = onSave.mock.calls[0][0];
    expect(saveResultAfter.referenceBranch).not.toEqual(null);
  });

  it("supports adding a treatment branch", async () => {
    const onSave = jest.fn();
    const { container } = render(
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

    selectFeatureConfig();
    await fillInBranch(container, `branch-reference`);

    onSave.mockClear();
    act(() => {
      fireEvent.click(screen.getByTestId("save-button"));
    });
    expect(onSave).toHaveBeenCalled();

    const saveResultBefore = onSave.mock.calls[0][0];
    expect(saveResultBefore.treatmentBranches).toEqual([]);

    act(() => {
      fireEvent.click(screen.getByTestId("add-branch"));
    });
    await fillInBranch(container, `branch-0`);

    onSave.mockClear();
    act(() => {
      fireEvent.click(screen.getByTestId("save-button"));
    });
    expect(onSave).toHaveBeenCalled();

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
    expect(saveResult.featureConfigId).toEqual(
      parseInt(MOCK_CONFIG.featureConfig![0]!.id, 10),
    );
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
    expect(saveResult.featureConfigId).toBeNull();
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

  it("updates save result with edits", async () => {
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
      featureEnabled: true,
    };

    for (const id of [`branch-reference`, `branch-${branchIdx}`]) {
      await fillInBranch(container, id, expectedData);
    }

    fireEvent.click(screen.getByTestId("save-button"));
    const saveResult = onSave.mock.calls[0][0];

    expect(saveResult.featureConfigId).toEqual(
      parseInt(MOCK_FEATURE_CONFIG_WITH_SCHEMA.id, 10),
    );
    expect(saveResult.referenceBranch).toEqual(expectedData);
    expect(saveResult.treatmentBranches[1]).toEqual(expectedData);
  });

  it("displays warning icon when reference branch is not set and server requires it", async () => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });

    const isMissingField = jest.fn(() => true);
    render(
      <SubjectBranches
        {...{
          isMissingField,
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              __typename: "NimbusReadyForReviewType",
              ready: false,
              message: {
                reference_branch: ["This field may not be null."],
              },
            },
          },
        }}
      />,
    );

    expect(isMissingField).toHaveBeenCalled();
    expect(screen.queryByTestId("missing-control")).toBeInTheDocument();
  });
});

async function fillInBranch(
  container: HTMLElement,
  id: string,
  expectedData = {
    name: "example name",
    description: "example description",
    ratio: "42",
    featureValue: "example value",
    featureEnabled: true,
  },
) {
  for (const [name, value] of Object.entries(expectedData)) {
    const field = container.querySelector(`#${id}-${name}`);
    expect(field).not.toBeNull();
    await act(async () => {
      fireEvent.change(field!, { target: { value } });
    });
  }
}

function selectFeatureConfig(featureIdx = 1) {
  act(() => {
    const featureConfigAddButton = screen.queryAllByTestId(
      "feature-config-add",
    )![0];
    fireEvent.click(featureConfigAddButton);
  });
  act(() => {
    const featureConfigSelects = screen.queryAllByTestId(
      "feature-config-select",
    )! as HTMLInputElement[];
    fireEvent.change(featureConfigSelects[0], {
      target: { value: featureIdx },
    });
  });
}
