/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { storiesOf } from "@storybook/react";
import React, { useState } from "react";
import { FormBranches } from ".";
import { SERVER_ERRORS } from "../../../lib/constants";
import {
  MOCK_ANNOTATED_BRANCH,
  MOCK_EXPERIMENT,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
  SubjectBranch,
  SubjectBranches,
} from "./mocks";

const onRemove = action("onRemove");
const onFeatureConfigChange = action("onFeatureConfigChange");
const onSave = action("onSave");
const onNext = action("onNext");

const commonFormBranchProps = {
  onRemove,
  onFeatureConfigChange,
};

const commonFormBranchesProps = { onSave, onNext };

storiesOf("pages/EditBranches/FormBranches/FormBranch", module)
  .add("reference branch", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureValue: null,
      }}
      isReference={true}
    />
  ))
  .add("treatment branch", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureValue: null,
      }}
    />
  ))
  .add("equal ratio", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      equalRatio
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureValue: null,
      }}
    />
  ))
  .add("with feature", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureEnabled: false,
        featureValue: "this is a default value",
      }}
    />
  ))
  .add("with feature value", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureEnabled: true,
        featureValue: "this is a default value",
      }}
    />
  ))
  .add("with several screenshots", () => (
    <SubjectBranch
      {...commonFormBranchProps}
      branch={{
        ...MOCK_ANNOTATED_BRANCH,
        featureEnabled: true,
        featureValue: "this is a default value",
        screenshots: [
          {
            description: "Meow meow.",
            image: "https://placekitten.com/1280/720",
          },
          {
            description: "Foo bar baz.",
            image: "https://via.placeholder.com/800x600.png?text=Screenshot",
          },
        ],
      }}
    />
  ));

storiesOf("pages/EditBranches/FormBranches", module)
  .add("empty", () => (
    <SubjectBranches
      {...commonFormBranchesProps}
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: null,
        treatmentBranches: null,
      }}
    />
  ))
  .add("with branches", () => <SubjectBranches {...commonFormBranchesProps} />)
  .add("with only one branch saved", () => (
    <SubjectBranches
      {...commonFormBranchesProps}
      experiment={{
        ...MOCK_EXPERIMENT,
        treatmentBranches: [
          {
            id: null,
            name: "",
            slug: "",
            description: "",
            ratio: 1,
            featureValue: null,
            featureEnabled: false,
            screenshots: [],
          },
        ],
      }}
    />
  ))
  .add("with equal ratio", () => (
    <SubjectBranches
      {...commonFormBranchesProps}
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: { ...MOCK_EXPERIMENT.referenceBranch!, ratio: 1 },
        treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch) => ({
          ...branch!,
          ratio: 1,
        })),
      }}
    />
  ))
  .add("with features", () => (
    <SubjectBranches
      {...commonFormBranchesProps}
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfigs: [MOCK_FEATURE_CONFIG],
      }}
    />
  ))
  .add("with feature values", () => (
    <SubjectBranches
      {...commonFormBranchesProps}
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SCHEMA],
      }}
    />
  ))
  .add("with review errors", () => (
    <SubjectBranches
      {...{
        ...commonFormBranchesProps,
      }}
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SCHEMA],
        readyForReview: {
          ready: false,
          message: {
            reference_branch: [SERVER_ERRORS.BLANK_DESCRIPTION],
            treatment_branches: [null, [SERVER_ERRORS.BLANK_DESCRIPTION]],
          },
          warnings: {},
        },
      }}
    />
  ))
  .add("with server/submit errors", () => {
    const [isLoading, setIsLoading] = useState(false);
    const [saveOrClear, setSaveOrClear] = useState(false);
    const onSave: React.ComponentProps<typeof FormBranches>["onSave"] = (
      saveState,
      setSubmitErrors,
      clearSubmitErrors,
    ) => {
      setIsLoading(true);
      setTimeout(() => {
        setIsLoading(false);
        // Toggle between clearing and raising simulated errors with each submit.
        setSaveOrClear(!saveOrClear);
        if (saveOrClear) {
          clearSubmitErrors();
        } else {
          // Kind of a random nonsensical assortment of errors, but want to
          // exercise errors scattered between branches and fields.
          setSubmitErrors({
            "*": ["Solar flares prevent submission."],
            feature_config: [
              "Feature Config required when a branch has feature enabled.",
            ],
            reference_branch: {
              name: ["This name stinks."],
              description: ["Try harder to describe this branch."],
              feature_value: ["ASCII art is not acceptable."],
              ratio: ["You call that a number?"],
            },
            treatment_branches: [
              {},
              {
                description: ["More errors."],
                feature_value: ["Yeah, no."],
                ratio: ["No roman numerals."],
              },
            ],
          });
        }
      }, 500);
    };

    return (
      <SubjectBranches
        {...{
          ...commonFormBranchesProps,
          isLoading,
          onSave,
          saveOnInitialRender: true,
        }}
        experiment={{
          ...MOCK_EXPERIMENT,
          featureConfigs: [MOCK_FEATURE_CONFIG_WITH_SCHEMA],
        }}
      />
    );
  });
