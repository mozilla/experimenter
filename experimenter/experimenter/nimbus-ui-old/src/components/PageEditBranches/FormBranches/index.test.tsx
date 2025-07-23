/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import selectEvent from "react-select-event";
import {
  MOCK_BRANCH,
  MOCK_EXPERIMENT,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
  MOCK_FEATURE_CONFIG_WITH_SETS_PREFS,
  SubjectBranches,
} from "src/components/PageEditBranches/FormBranches/mocks";
import { AnnotatedBranch } from "src/components/PageEditBranches/FormBranches/reducer";
import {
  extractUpdateBranch,
  FormData,
} from "src/components/PageEditBranches/FormBranches/reducer/update";
import { SERVER_ERRORS } from "src/lib/constants";
import { mockExperimentQuery, MOCK_CONFIG } from "src/lib/mocks";
import { assertSerializerMessages } from "src/lib/test-utils";
import {
  NimbusExperimentApplicationEnum,
  NimbusExperimentFirefoxVersionEnum,
} from "src/types/globalTypes";

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
    const formData: FormData = {
      referenceBranch: {
        featureValues: [
          {
            featureConfig:
              MOCK_EXPERIMENT.referenceBranch!.featureValues![0]!.featureConfig!.id!.toString(),
            value: MOCK_EXPERIMENT.referenceBranch!.featureValues![0]!.value,
          },
        ],
      },
      treatmentBranches: [
        {
          featureValues: [
            {
              featureConfig:
                MOCK_EXPERIMENT.treatmentBranches![0]!.featureValues![0]!.featureConfig!.id!.toString(),
              value:
                MOCK_EXPERIMENT.treatmentBranches![0]!.featureValues![0]!.value,
            },
          ],
        },
        {
          featureValues: [
            {
              featureConfig:
                MOCK_EXPERIMENT.treatmentBranches![1]!.featureValues![0]!.featureConfig!.id!.toString(),
              value:
                MOCK_EXPERIMENT.treatmentBranches![1]!.featureValues![0]!.value,
            },
          ],
        },
      ],
    };
    render(<SubjectBranches {...{ onSave }} />);
    await clickAndWaitForSave(onSave);
    const onSaveArgs = onSave.mock.calls[0];
    const expectedData = {
      featureConfigIds: [],
      referenceBranch: extractUpdateBranch(
        MOCK_EXPERIMENT.referenceBranch! as AnnotatedBranch,
        formData.referenceBranch,
      ),
      treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch, idx) =>
        extractUpdateBranch(
          branch! as AnnotatedBranch,
          formData.treatmentBranches![idx],
        ),
      ),
      isRollout: false,
      preventPrefConflicts: false,
      warnFeatureSchema: false,
      isLocalized: false,
      localizations: null,
    };
    expect(onSaveArgs[0]).toEqual(expectedData);
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

  it("removes treatment branches when isRollout checkbox enabled", async () => {
    const onSave = jest.fn();
    const { container } = render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            treatmentBranches: [
              {
                id: null,
                name: "",
                slug: "",
                description: "",
                ratio: 0,
                featureValues: [],
                screenshots: [],
              },
            ],
          },
        }}
      />,
    );

    fireEvent.click(screen.getByTestId("is-rollout-checkbox"));
    await clickAndWaitForSave(onSave);

    const saveResult = onSave.mock.calls[0][0];
    await waitFor(() => {
      expect(saveResult.treatmentBranches).toEqual([]);
    });
  });

  it("renders options", async () => {
    const { container } = render(
      <SubjectBranches experiment={{ ...MOCK_EXPERIMENT }} />,
    );
    const select = screen.getByLabelText("Features");

    let options = container.querySelectorAll(
      "#react-select-feature-configs-listbox .react-select__option",
    );
    expect(options.length).toEqual(0);

    await selectEvent.openMenu(select);

    options = container.querySelectorAll(
      "#react-select-feature-configs-listbox .react-select__option",
    );
    expect(options.length).toEqual(4);
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
            treatmentBranches: [],
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
    await selectFeatureConfigs([1]);
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
              featureValues: [],
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
            treatmentBranches: [],
          },
        }}
      />,
    );

    await selectFeatureConfigs([1]);
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

  it("displays an error message when Rollouts are not supported", async () => {
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
              featureValues: [],
              screenshots: [],
            },
            treatmentBranches: null,
            isRollout: true,
          },
          onSave,
        }}
      />,
    );
    expect(screen.getByText(ROLLOUT_WARNING));
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
    await selectFeatureConfigs([expectedFeatureId!]);
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
      description: "example description",
      featureValues: [
        {
          featureConfig: "1",
          value: "example value",
        },
      ],
      id: 123,
      name: "example name",
      ratio: 42,
      screenshots: [],
    };
    const inputData = [
      ["name", expectedData.name],
      ["description", expectedData.description],
      ["ratio", expectedData.ratio],
      ["featureValues[0].value", expectedData.featureValues[0].value],
    ];

    for (const id of ["referenceBranch", `treatmentBranches[${branchIdx}]`]) {
      await fillInBranch(container, id, inputData);
    }

    await clickAndWaitForSave(onSave);
    const saveResult = onSave.mock.calls[0][0];

    expect(saveResult.featureConfigIds).toEqual([
      MOCK_FEATURE_CONFIG_WITH_SCHEMA.id,
    ]);
    expect(saveResult.referenceBranch).toEqual({
      ...expectedData,
      id: MOCK_EXPERIMENT.referenceBranch!.id,
    });
    expect(saveResult.treatmentBranches[1]).toEqual({
      ...expectedData,
      id: MOCK_EXPERIMENT.treatmentBranches![1]!.id,
    });
  });

  it("can display server review-readiness messages", async () => {
    await assertSerializerMessages(SubjectBranches, {
      feature_configs: [SERVER_ERRORS.FEATURE_CONFIGS],
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
    expect(screen.getAllByText(SERVER_ERRORS.FEATURE_CONFIGS)).toHaveLength(1);
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
                feature_configs: [SERVER_ERRORS.FEATURE_CONFIGS],
                reference_branch: {
                  description: [SERVER_ERRORS.BLANK_DESCRIPTION],
                },
              },
              warnings: {
                reference_branch: {
                  feature_values: [{ value: [FEATURE_VALUE_WARNING] }],
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
                featureValues: [],
                screenshots: [],
              },
            ],
          },
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByText(SERVER_ERRORS.FEATURE_CONFIGS)).toHaveLength(
        1,
      );
      expect(screen.getAllByText(FEATURE_VALUE_WARNING)).toHaveLength(1);
    });
  });

  it("disables save buttons when archived", async () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: {
              ...MOCK_EXPERIMENT.referenceBranch!,
              screenshots: [],
            },
            isArchived: true,
          },
        }}
      />,
    );
    expect(screen.getByTestId("save-button")).toBeDisabled();
    expect(screen.getByTestId("next-button")).toBeDisabled();
  });

  it("enables save buttons when not archived", async () => {
    const onSave = jest.fn();
    render(
      <SubjectBranches
        {...{
          onSave,
          experiment: {
            ...MOCK_EXPERIMENT,
            referenceBranch: {
              ...MOCK_EXPERIMENT.referenceBranch!,
              screenshots: [],
            },
          },
        }}
      />,
    );
    expect(screen.getByTestId("save-button")).toBeEnabled();
    expect(screen.getByTestId("next-button")).toBeEnabled();
  });

  describe("preventPrefConflicts checkbox", () => {
    it("doesn't render if no feature config set", () => {
      render(
        <SubjectBranches
          experiment={{ ...MOCK_EXPERIMENT, featureConfigs: [] }}
        />,
      );

      expect(
        screen.queryByTestId("prevent-pref-conflicts-checkbox"),
      ).not.toBeInTheDocument();
    });

    it("doesn't render if the set feature config does not set prefs", () => {
      render(
        <SubjectBranches
          experiment={{
            ...MOCK_EXPERIMENT,
            featureConfigs: [MOCK_FEATURE_CONFIG],
          }}
        />,
      );

      expect(
        screen.queryByTestId("prevent-pref-conflicts-checkbox"),
      ).not.toBeInTheDocument();
    });

    it("does render if the set feature config does set prefs", () => {
      render(
        <SubjectBranches
          experiment={{
            ...MOCK_EXPERIMENT,
            featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SETS_PREFS],
          }}
        />,
      );

      const checkbox = screen.getByTestId(
        "prevent-pref-conflicts-checkbox",
      ) as HTMLInputElement;
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.checked).toEqual(false);
    });

    it("resets when switching away from a feature config that sets prefs", async () => {
      render(
        <SubjectBranches
          experiment={{
            ...MOCK_EXPERIMENT,
            featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SETS_PREFS],
          }}
        />,
      );

      {
        const checkbox = screen.getByTestId(
          "prevent-pref-conflicts-checkbox",
        ) as HTMLInputElement;

        expect(checkbox).toBeInTheDocument();
        expect(checkbox.checked).toEqual(false);

        await userEvent.click(checkbox);
        expect(checkbox.checked).toEqual(true);
      }

      await selectFeatureConfigs([MOCK_FEATURE_CONFIG.id!], { clear: true });

      await waitFor(() => {
        expect(
          screen.queryByTestId("prevent-pref-conflicts-checkbox"),
        ).toBeNull();
      });

      await selectFeatureConfigs([MOCK_FEATURE_CONFIG_WITH_SETS_PREFS.id!], {
        clear: true,
      });

      {
        const checkbox = screen.getByTestId(
          "prevent-pref-conflicts-checkbox",
        ) as HTMLInputElement;

        expect(checkbox).toBeInTheDocument();
        expect(checkbox.checked).toEqual(false);
      }
    });
  });

  it("renders localization checkbox", async () => {
    const { experiment } = mockExperimentQuery("boo");

    render(<SubjectBranches {...{ experiment }} />);
    const checkbox = screen.getByTestId("isLocalized");

    expect(checkbox).toBeInTheDocument();
  });

  it("renders localized content text field when localization checkbox is checked", async () => {
    const { experiment } = mockExperimentQuery("boo");
    render(<SubjectBranches {...{ experiment }} />);

    const checkbox = screen.getByTestId("isLocalized");
    fireEvent.click(checkbox);
    const textField = screen.getByTestId("localizations");

    expect(textField).toBeInTheDocument();
  });

  it("renders localized content from experiment", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      isLocalized: true,
      localizations: "This is localized content",
    });

    render(<SubjectBranches {...{ experiment }} />);
    const checkbox = screen.getByTestId("isLocalized") as HTMLInputElement;
    const textField = screen.getByTestId("localizations");

    expect(checkbox.checked).toEqual(true);
    expect(textField).toHaveValue(experiment.localizations);
  });

  it("does not render localized content for non-desktop applications", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      application: NimbusExperimentApplicationEnum.IOS,
    });

    render(<SubjectBranches {...{ experiment }} />);

    expect(screen.queryByTestId("isLocalized")).toBeNull();
    expect(screen.queryByTestId("localizations")).toBeNull();
  });

  it("unchecking isLocalized clears localizations form data", async () => {
    const onSave = jest.fn();
    const { experiment } = mockExperimentQuery("boo", {
      isLocalized: true,
      localizations: "This is localized content",
    });

    render(<SubjectBranches {...{ experiment, onSave }} />);

    const checkbox = screen.getByTestId("isLocalized") as HTMLInputElement;

    await userEvent.click(checkbox);

    expect(screen.queryByTestId("localizations")).toBeNull();

    await clickAndWaitForSave(onSave);

    expect(onSave.mock.calls[0][0]).toEqual(
      expect.objectContaining({
        isLocalized: false,
        localizations: null,
      }),
    );
  });

  it("changing localizations field updates on save", async () => {
    const onSave = jest.fn();
    const { experiment } = mockExperimentQuery("boo", {
      isLocalized: true,
      localizations: "This is localized content",
    });

    render(<SubjectBranches {...{ experiment, onSave }} />);

    await userEvent.type(
      screen.getByTestId("localizations"),
      "{selectall}{backspace}updated localizations",
    );

    await clickAndWaitForSave(onSave);

    expect(onSave.mock.calls[0][0]).toEqual(
      expect.objectContaining({
        isLocalized: true,
        localizations: "updated localizations",
      }),
    );
  });

  it("allows multiple values to be selected", async () => {
    const onSave = jest.fn();
    const { experiment } = mockExperimentQuery("slug");
    const { container } = render(
      <SubjectBranches {...{ experiment, onSave }} />,
    );

    let selected = container.querySelectorAll(
      ".react-select__multi-value__label",
    );

    expect(selected.length).toEqual(1);
    expect(selected[0].textContent).toEqual(
      MOCK_CONFIG.allFeatureConfigs![0]!.name,
    );

    await selectFeatureConfigs([2]);

    selected = container.querySelectorAll(".react-select__multi-value__label");
    expect(selected.length).toEqual(2);
    expect(selected[0].textContent).toEqual(
      MOCK_CONFIG.allFeatureConfigs![0]!.name,
    );
    expect(selected[1].textContent).toEqual(
      MOCK_CONFIG.allFeatureConfigs![1]!.name,
    );

    await clickAndWaitForSave(onSave);

    const payload = onSave.mock.calls[0][0];
    expect(payload.featureConfigIds).toEqual([1, 2]);
    expect(payload.referenceBranch.featureValues).toEqual([
      {
        featureConfig: "1",
        value: '{"environmental-fact": "really-citizen"}',
      },
      {
        featureConfig: "2",
        value: "",
      },
    ]);

    expect(payload.treatmentBranches.length).toEqual(1);
    expect(payload.treatmentBranches[0].featureValues).toEqual([
      {
        featureConfig: "1",
        value: '{"effect-effect-whole": "close-teach-exactly"}',
      },
      {
        featureConfig: "2",
        value: "",
      },
    ]);
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
  expectedData = [
    ["name", "example name"],
    ["description", "example description"],
    ["ratio", 42],
    ["featureValues[0].value", '{"key": "value"}'],
  ],
) {
  for (const [name, value] of expectedData) {
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

async function selectFeatureConfigs(
  featureConfigIds: number[],
  { clear = false }: { clear?: boolean } = {},
) {
  const featureConfigsSelect = screen.getByLabelText("Features");

  if (clear) {
    await selectEvent.clearAll(featureConfigsSelect);
  }

  if (featureConfigIds.length) {
    await selectEvent.select(featureConfigsSelect, (content, el) => {
      if (!el) {
        return false;
      }
      const featureConfigId = el.getAttribute("data-feature-config-id");
      if (!featureConfigId) {
        return false;
      }

      return featureConfigIds.includes(parseInt(featureConfigId));
    });
  }
}
