/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import {
  MOCK_ANNOTATED_BRANCH,
  SubjectBranch,
} from "src/components/PageEditBranches/FormBranches/mocks";
import { FIELD_MESSAGES } from "src/lib/constants";

describe("FormBranch", () => {
  it("renders as expected", () => {
    render(<SubjectBranch />);
    expect(screen.getByTestId("FormBranch")).toBeInTheDocument();
    expect(screen.queryByTestId("control-pill")).not.toBeInTheDocument();
    expect(screen.queryByTestId("equal-ratio")).not.toBeInTheDocument();
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

  it("displays feature value edit when value is non-null", () => {
    render(
      <SubjectBranch
        branch={{
          ...MOCK_ANNOTATED_BRANCH,
          featureValues: [{ value: "this is a default value" }],
        }}
      />,
    );
    expect(
      screen.queryByTestId("referenceBranch.featureValues[0].value"),
    ).toBeInTheDocument();
  });

  it("calls onRemove when the branch remove button is clicked", async () => {
    const onRemove = jest.fn();
    render(<SubjectBranch {...{ onRemove }} />);
    fireEvent.click(screen.getByTestId("remove-branch"));
    expect(onRemove).toHaveBeenCalled();
  });

  it("requires ratio to be a number", async () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
    };
    const { container } = render(<SubjectBranch {...{ branch }} />);
    const field = screen.getByTestId("referenceBranch.ratio");
    act(() => {
      fireEvent.change(field, { target: { value: "abc" } });
      fireEvent.blur(field);
    });
    await assertInvalidField(container, "referenceBranch.ratio");
    expect(
      container.querySelector(
        ".invalid-feedback[data-for='referenceBranch.ratio']",
      ),
    ).toHaveTextContent(FIELD_MESSAGES.NUMBER);
  });

  it("displays expected message on required fields", async () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
    };
    const { container } = render(<SubjectBranch {...{ branch }} />);
    const field = screen.getByTestId("referenceBranch.name");
    act(() => {
      fireEvent.change(field, { target: { value: "" } });
      fireEvent.blur(field);
    });
    await assertInvalidField(container, "referenceBranch.name");
    expect(
      container.querySelector(
        ".invalid-feedback[data-for='referenceBranch.name']",
      ),
    ).toHaveTextContent(FIELD_MESSAGES.REQUIRED);
  });

  it("should display server-side errors even when client-side validation is not defined", async () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
      errors: {
        description: ["This description is boring"],
      },
    };
    const { container } = render(<SubjectBranch branch={branch} />);
    await assertInvalidField(container, "referenceBranch.description");
  });

  it("does not render FormFeatureValue when no values features are selected", () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
      featureValues: [],
    };

    render(<SubjectBranch branch={branch} />);

    expect(
      screen.queryByTestId("referenceBranch.featureValues[0].value"),
    ).toBeNull();
  });

  it("renders FormFeatureValue for each feature selected", () => {
    const branch = {
      ...MOCK_ANNOTATED_BRANCH,
      featureValues: [
        {
          featureConfig: "1",
          value: `{"value": "foo"}`,
        },
        {
          featureConfig: "3",
          value: `{"value": "bar"}`,
        },
        {
          featureConfig: "5",
          value: `{"value": "baz"}`,
        },
      ],
    };

    render(<SubjectBranch branch={branch} />);

    const inputs = [
      screen.getByTestId(
        "referenceBranch.featureValues[0].value",
      ) as HTMLTextAreaElement,
      screen.getByTestId(
        "referenceBranch.featureValues[1].value",
      ) as HTMLTextAreaElement,
      screen.getByTestId(
        "referenceBranch.featureValues[2].value",
      ) as HTMLTextAreaElement,
    ];

    for (let i = 0; i < 3; i++) {
      expect(inputs[i].value).toEqual(branch.featureValues[i].value);
    }
  });

  const assertInvalidField = async (container: HTMLElement, testId: string) => {
    await waitFor(() => {
      expect(screen.getByTestId(testId)).toHaveClass("is-invalid");
      expect(container.querySelector(`[data-for="${testId}"]`)).toHaveClass(
        "invalid-feedback",
      );
    });
  };
});
