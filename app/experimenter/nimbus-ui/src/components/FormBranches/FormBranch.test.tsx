/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";

import { MOCK_CONFIG } from "../../lib/mocks";
import {
  SubjectBranch,
  MOCK_ANNOTATED_BRANCH,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
} from "./mocks";

describe("FormBranch", () => {
  it("renders as expected", () => {
    render(<SubjectBranch />);
    expect(screen.getByTestId("FormBranch")).toBeInTheDocument();
    expect(screen.queryByTestId("control-pill")).not.toBeInTheDocument();
    expect(screen.queryByTestId("equal-ratio")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-edit")).toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-add")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("does nothing on form submission", () => {
    render(<SubjectBranch />);
    const form = screen.getByTestId("FormBranch");
    fireEvent.submit(form);
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
      <SubjectBranch
        branch={{ ...MOCK_ANNOTATED_BRANCH, featureEnabled: false }}
      />,
    );
    const featureSwitchLabel = container.querySelector(
      "label[for=demo-featureEnabled]",
    );
    expect(featureSwitchLabel).toHaveTextContent("Off");
  });

  it("hides feature configuration edit when feature not selected", () => {
    render(
      <SubjectBranch
        branch={MOCK_ANNOTATED_BRANCH}
        experimentFeatureConfig={null}
      />,
    );
    expect(screen.queryByTestId("feature-config-edit")).not.toBeInTheDocument();
    expect(screen.queryByTestId("feature-config-add")).toBeInTheDocument();
  });

  it("hides feature value edit when schema is null", () => {
    render(
      <SubjectBranch
        branch={{
          ...MOCK_ANNOTATED_BRANCH,
        }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("hides feature value edit when feature disabled", () => {
    render(
      <SubjectBranch
        branch={{ ...MOCK_ANNOTATED_BRANCH, featureEnabled: false }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).not.toBeInTheDocument();
  });

  it("displays feature value edit when value is non-null", () => {
    render(
      <SubjectBranch
        branch={{
          ...MOCK_ANNOTATED_BRANCH,
          featureValue: "this is a default value",
          featureEnabled: true,
        }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      />,
    );
    expect(screen.queryByTestId("feature-value-edit")).toBeInTheDocument();
  });

  it("calls onFeatureConfigChange with selected feature", async () => {
    const featureIdx = 1;
    const onFeatureConfigChange = jest.fn();
    render(<SubjectBranch {...{ onFeatureConfigChange }} />);
    fireEvent.change(screen.getByTestId("feature-config-select"), {
      target: { value: featureIdx },
    });
    expect(onFeatureConfigChange).toHaveBeenCalledWith(
      MOCK_CONFIG!.featureConfig![featureIdx],
    );
  });

  it("calls onFeatureConfigChange with null when blank feature selected", async () => {
    const onFeatureConfigChange = jest.fn();
    render(<SubjectBranch {...{ onFeatureConfigChange }} />);
    fireEvent.change(screen.getByTestId("feature-config-select"), {
      target: { value: "" },
    });
    expect(onFeatureConfigChange).toHaveBeenCalledWith(null);
  });

  it("calls onRemove when the branch remove button is clicked", async () => {
    const onRemove = jest.fn();
    render(<SubjectBranch {...{ onRemove }} />);
    fireEvent.click(screen.getByTestId("remove-branch"));
    expect(onRemove).toHaveBeenCalled();
  });

  it("calls onChange when branch fields are edited", async () => {
    const id = "testing123";
    const onChange = jest.fn();
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
      featureValue: "this is a default value",
      featureEnabled: true,
    };

    const { container } = render(
      <SubjectBranch
        {...{ id, onChange, branch }}
        experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      />,
    );

    const expectedData = {
      name: "example name",
      description: "example description",
      ratio: "42",
      featureValue: "example value",
    };

    for (const [name, value] of Object.entries(expectedData)) {
      onChange.mockClear();
      const field = container.querySelector(`#${id}-${name}`);
      expect(field).not.toBeNull();
      await act(async () => {
        fireEvent.change(field!, { target: { value } });
      });
      expect(onChange).toHaveBeenCalledWith({ ...branch, [name]: value });
    }

    await act(async () => {
      fireEvent.click(container.querySelector(`#${id}-featureEnabled`)!);
    });
    expect(onChange).toHaveBeenCalledWith({ ...branch, featureEnabled: false });
  });

  it("should display server-side errors but hide when field touched", async () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
      errors: {
        name: ["This name is trouble"],
      },
    };

    const { container } = render(<SubjectBranch branch={branch} />);
    expect(container.querySelector("[data-for=demo-name]")).toHaveClass(
      "invalid-feedback",
    );

    const field = container.querySelector(`#demo-name`)!;
    expect(field).not.toBeNull();
    await act(async () => {
      fireEvent.change(field, { target: { value: "new value" } });
      fireEvent.blur(field);
    });

    expect(container.querySelector("[data-for=demo-name]")).toBeNull();
  });
});
