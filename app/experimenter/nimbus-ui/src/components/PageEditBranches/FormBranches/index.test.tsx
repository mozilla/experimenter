/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { SERVER_ERRORS } from "../../../lib/constants";
import { MOCK_CONFIG } from "../../../lib/mocks";
import { assertSerializerMessages } from "../../../lib/test-utils";
import {
  NimbusExperimentApplicationEnum,
  NimbusExperimentFirefoxVersionEnum,
} from "../../../types/globalTypes";
import {
  MOCK_BRANCH,
  MOCK_EXPERIMENT,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
  SubjectBranches,
} from "./mocks";
import { extractUpdateBranch } from "./reducer/update";

describe("FormBranches", () => {
  it("renders as expected", async () => {
    render(<SubjectBranches />);
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("add-branch")).toBeInTheDocument();
    const branches = screen.queryAllByTestId("FormBranch");
    expect(branches.length).toEqual(
      MOCK_EXPERIMENT!.treatmentBranches!.length + 1,
    );
  });

  it("hides the add branch button for a rollout", async () => {
    render(
      <SubjectBranches experiment={{ ...MOCK_EXPERIMENT, isRollout: true }} />,
    );
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.queryByTestId("add-branch")).not.toBeInTheDocument();
  });

  it("renders as expected while loading", async () => {
    const onSave = jest.fn();
    const onNext = jest.fn();
    render(<SubjectBranches {...{ isLoading: true, onSave, onNext }} />);
    expect(screen.getByTestId("FormBranches")).toBeInTheDocument();
    expect(screen.getByTestId("save-button")).toHaveTextContent("Saving");
    clickSave();
    expect(onSave).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("next-button"));
    expect(onNext).not.toHaveBeenCalled();
  });

  it("calls onSave with extracted update when save button clicked", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    await clickAndWaitForSave(onSave);
    const onSaveArgs = onSave.mock.calls[0];
    expect(onSaveArgs[0]).toEqual({
      featureConfigIds: [],
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
    const onSave = jest.fn((state, setSubmitErrors) => {
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
        container.querySelector('*[data-for="referenceBranch.name"]'),
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
    const { container } = render(<SubjectBranches {...{ onSave }} />);
    await clickAndWaitForSave(onSave);
    await waitFor(() => {
      expect(screen.queryByTestId("global-error")).not.toBeInTheDocument();
      expect(
        container.querySelector('*[data-for="branch-reference-name"]'),
      ).not.toBeInTheDocument();
    });
  });

  it("displays exception thrown by onSaveHandler", async () => {
    const expectedErrorMessage = "Super bad thing happened";
    const onSave = jest.fn(() => {
      throw new Error(expectedErrorMessage);
    });
    render(<SubjectBranches {...{ onSave }} />);
    await clickAndWaitForSave(onSave);
    await waitFor(() => {
      expect(screen.getByTestId("global-error")).toHaveTextContent(
        expectedErrorMessage,
      );
    });
  });

  it("sets all branch ratios to 1 when equal ratio checkbox enabled", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(screen.getByTestId("equal-ratio-checkbox"));
    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.referenceBranch.ratio).toEqual(1);
    for (const branch of saveResult.treatmentBranches) {
      expect(branch.ratio).toEqual(1);
    }
  });

  it("sets warnFeatureSchema when checkbox enabled", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(
      screen.getByTestId("equal-warn-on-feature-value-schema-invalid-checkbox"),
    );
    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.warnFeatureSchema).toBeTruthy();
  });

  it("sets isRollout when checkbox enabled", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    fireEvent.click(screen.getByTestId("is-rollout-checkbox"));
    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.isRollout).toBeTruthy();
  });

  it("gracefully handles selecting an invalid feature config", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    selectFeatureConfig(null);
    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];
    expect(saveResult.featureConfigIds).toEqual([]);
  });

  it("requires adding a valid control branch before save is completed", async () => {
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

    clickSave();
    await waitFor(() => {
      expect(screen.getByTestId("global-error")).toHaveTextContent(
        "Control branch is required",
      );
    });

    fireEvent.click(screen.getByTestId("add-branch"));
    selectFeatureConfig();
    await fillInBranch(container, "referenceBranch");
    expect(screen.getByTestId("save-button")).not.toBeDisabled();

    await clickAndWaitForSave(onSave);
    await waitFor(() => {
      expect(onSave.mock.calls[0][0].referenceBranch).not.toEqual(null);
    });
  });

  it("requires only a branch name before save", async () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: {
              id: null,
              name: "",
              slug: "",
              description: "",
              ratio: 1,
              featureValue: null,
              featureEnabled: false,
              screenshots: [],
            },
            treatmentBranches: null,
          },
        }}
      />,
    );

    const field = screen.getByTestId("referenceBranch.name");
    fireEvent.change(field, { target: { value: "Big beautiful branch" } });
    fireEvent.blur(field);

    await clickAndWaitForSave(onSave);
  });

  it("supports adding a screenshot to a branch", async () => {
    render(
      <SubjectBranches
        {...{
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: {
              ...MOCK_EXPERIMENT.referenceBranch!,
              screenshots: [],
            },
            treatmentBranches: null,
          },
        }}
      />,
    );
    expect(screen.queryAllByTestId("FormScreenshot").length).toEqual(0);
    fireEvent.click(screen.getByTestId("add-screenshot"));
    await waitFor(() => {
      expect(screen.queryAllByTestId("FormScreenshot").length).toEqual(1);
    });
  });

  it("supports removing a screenshot from a branch", async () => {
    render(
      <SubjectBranches
        {...{
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: {
              ...MOCK_EXPERIMENT.referenceBranch!,
              screenshots: [
                {
                  id: 123,
                  description: "remove me",
                  image: "http://example.com/image.png",
                },
              ],
            },
            treatmentBranches: null,
          },
        }}
      />,
    );
    expect(screen.queryAllByTestId("FormScreenshot").length).toEqual(1);
    fireEvent.click(screen.getByTestId("remove-screenshot"));
    await waitFor(() => {
      expect(screen.queryAllByTestId("FormScreenshot").length).toEqual(0);
    });
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
    await fillInBranch(container, "referenceBranch");

    onSave.mockClear();
    await clickAndWaitForSave(onSave);

    const saveResultBefore = onSave.mock.calls[0][0];
    expect(saveResultBefore.treatmentBranches).toEqual([]);

    onSave.mockClear();
    fireEvent.click(screen.getByTestId("add-branch"));
    await fillInBranch(container, "treatmentBranches[0]");
    await clickAndWaitForSave(onSave);

    const saveResultAfter = onSave.mock.calls[0][0];
    expect(saveResultAfter.treatmentBranches).not.toEqual(null);
  });

  it("Rollout support error", async () => {
    const onSave = jest.fn();
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });
    const ROLLOUT_WARNING =
      "Rollouts are not supported for the selected version";
    render(
      <SubjectBranches
        {...{
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              ready: false,
              message: {
                is_rollout: [ROLLOUT_WARNING],
              },
              warnings: {},
            },
            application: NimbusExperimentApplicationEnum.DESKTOP,
            firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_106,
            referenceBranch: {
              id: null,
              name: "test",
              slug: "",
              description: "test",
              ratio: 1,
              featureValue: null,
              featureEnabled: false,
              screenshots: [],
            },
            treatmentBranches: null,
            isRollout: true,
          },
          onSave,
        }}
      />,
    );
    expect(screen.getAllByText(ROLLOUT_WARNING)).toHaveLength(1);
  });

  it("supports removing a treatment branch", async () => {
    const onSave = jest.fn();
    render(<SubjectBranches {...{ onSave }} />);
    const removeFirst = screen.queryAllByTestId("remove-branch")![0];
    fireEvent.click(removeFirst);
    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];
    const expectedDeletedBranch = MOCK_EXPERIMENT.treatmentBranches![0]!;
    expect(
      saveResult.treatmentBranches.findIndex(
        (branch: typeof MOCK_BRANCH) =>
          branch.slug === expectedDeletedBranch.slug,
      ),
    ).toEqual(-1);
  });

  it("supports adding feature config", async () => {
    const onSave = jest.fn();
    const expectedFeatureId = MOCK_CONFIG.allFeatureConfigs![1]!.id;
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfigs: [],
          },
        }}
      />,
    );
    selectFeatureConfig(expectedFeatureId);
    await clickAndWaitForSave(onSave);
    expect(onSave.mock.calls[0][0].featureConfigIds).toEqual([
      expectedFeatureId,
    ]);
  });

  it("updates save result with edits", async () => {
    const onSave = jest.fn();
    const { container } = render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SCHEMA],
          },
        }}
      />,
    );
    const branchIdx = 1;

    const expectedData = {
      name: "example name",
      description: "example description",
      ratio: 42,
      featureValue: "example value",
      featureEnabled: true,
    };

    for (const id of ["referenceBranch", `treatmentBranches[${branchIdx}]`]) {
      await fillInBranch(container, id, expectedData);
    }

    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];

    expect(saveResult.featureConfigIds).toEqual([
      MOCK_FEATURE_CONFIG_WITH_SCHEMA.id,
    ]);
    expect(saveResult.referenceBranch).toEqual({
      id: MOCK_EXPERIMENT.referenceBranch!.id,
      screenshots: [],
      ...expectedData,
    });
    expect(saveResult.treatmentBranches[1]).toEqual({
      id: MOCK_EXPERIMENT.treatmentBranches![1]!.id,
      screenshots: [],
      ...expectedData,
    });
  });

  it("can display server review-readiness messages", async () => {
    await assertSerializerMessages(SubjectBranches, {
      feature_config: [SERVER_ERRORS.FEATURE_CONFIG],
      reference_branch: {
        name: ["Drop a heart", "and break a name"],
        description: [
          "We're always sleeping in and sleeping",
          "For the wrong team",
        ],
      },
      treatment_branches: [
        {
          name: ["We're going down"],
          description: ["Down in an earlier round"],
        },
      ],
    });

    // Feature config review-readiness errors are displayed on branches
    expect(screen.getAllByText(SERVER_ERRORS.FEATURE_CONFIG)).toHaveLength(1);
  });

  it("doesn't display feature_config review-readiness message on an unsaved branch", async () => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });

    const FEATURE_VALUE_WARNING =
      "'sdf' does not match any of the regexes: 'foo'";

    render(
      <SubjectBranches
        {...{
          experiment: {
            ...MOCK_EXPERIMENT,
            readyForReview: {
              ready: false,
              message: {
                feature_config: [SERVER_ERRORS.FEATURE_CONFIG],
                reference_branch: {
                  description: [SERVER_ERRORS.BLANK_DESCRIPTION],
                },
              },
              warnings: {
                reference_branch: {
                  feature_value: [FEATURE_VALUE_WARNING],
                },
              },
            },
            referenceBranch: {
              ...MOCK_EXPERIMENT.referenceBranch!,
              name: "",
              slug: "",
            },
            treatmentBranches: [
              {
                id: null,
                name: "",
                slug: "",
                description: "",
                ratio: 0,
                featureValue: null,
                featureEnabled: false,
                screenshots: [],
              },
            ],
          },
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByText(SERVER_ERRORS.FEATURE_CONFIG)).toHaveLength(1);
      expect(screen.getAllByText(FEATURE_VALUE_WARNING)).toHaveLength(1);
    });
  });
});

const clickSave = () => fireEvent.click(screen.getByTestId("save-button"));

const clickAndWaitForSave = async (pendingOnSave: jest.Mock<any, any>) => {
  clickSave();
  await waitFor(() => expect(pendingOnSave).toHaveBeenCalled());
};

async function fillInBranch(
  container: HTMLElement,
  fieldNamePrefix: string,
  expectedData = {
    name: "example name",
    description: "example description",
    ratio: 42,
    featureValue: "example value",
    featureEnabled: true,
  },
) {
  for (const [name, value] of Object.entries(expectedData)) {
    const field = container.querySelector(
      `[name="${fieldNamePrefix}.${name}"]`,
    ) as HTMLInputElement;
    expect(field).not.toBeNull();
    fireEvent.focus(field!);
    fireEvent.change(field!, { target: { value } });
    fireEvent.blur(field!);
    await waitFor(() => {
      // HACK: the field value is always a string, regardless of input value type
      expect(field.value).toEqual("" + value);
    });
  }
}

function selectFeatureConfig(featureIdx: number | null = 1) {
  const featureConfigSelects = screen.getByTestId(
    "feature-config-select",
  ) as HTMLInputElement;
  fireEvent.change(featureConfigSelects, {
    target: { value: featureIdx },
  });
}
