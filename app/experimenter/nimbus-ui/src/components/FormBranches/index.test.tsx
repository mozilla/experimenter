/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";

import {
  SubjectBranch,
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
});

describe("FormBranch", () => {
  it("renders as expected", async () => {
    render(<SubjectBranch />);
    expect(screen.getByTestId("FormBranch")).toBeInTheDocument();
    expect(screen.queryByTestId("control-pill")).not.toBeInTheDocument();
    expect(screen.queryByTestId("equal-ratio")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-edit")).toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-add")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("includes a control label when reference branch", () => {
    render(<SubjectBranch isReference />);
    expect(screen.getByTestId("control-pill")).toBeInTheDocument();
  });

  it("indicates equal ratio when enabled", () => {
    render(<SubjectBranch equalRatio />);
    expect(screen.getByTestId("equal-ratio")).toBeInTheDocument();
  });

  it("reflects when feature is disabled", () => {
    const { container } = render(
      <SubjectBranch branch={{ ...MOCK_BRANCH, featureEnabled: false }} />,
    );
    const featureSwitchLabel = container.querySelector(
      "label[for=featureEnabled]",
    );
    expect(featureSwitchLabel).toHaveTextContent("Off");
  });

  it("hides feature configuration edit when feature not selected", () => {
    render(
      <SubjectBranch branch={MOCK_BRANCH} experimentFeatureConfig={null} />,
    );
    expect(screen.queryByTestId("feature-config-edit")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-add")).toBeInTheDocument();
  });

  it("hides feature value edit when schema is null", () => {
    render(
      <SubjectBranch
        branch={{
          ...MOCK_BRANCH,
        }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("hides feature value edit when feature disabled", () => {
    render(
      <SubjectBranch
        branch={{ ...MOCK_BRANCH, featureEnabled: false }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("displays feature value edit when value is non-null", () => {
    render(
      <SubjectBranch
        branch={{
          ...MOCK_BRANCH,
          featureValue: "this is a default value",
          featureEnabled: true,
        }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).toBeInTheDocument();
  });
});
