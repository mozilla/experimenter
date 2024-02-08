/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  act as hookAct,
  renderHook,
  RenderResult as HookRenderResult,
} from "@testing-library/react-hooks";
import React from "react";
import { act } from "react-dom/test-utils";
import { Subject as BaseSubject } from "src/components/Summary/TableQA/mocks";
import useQA, { UseQAResult } from "src/components/Summary/TableQA/useQA";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import {
  CHANGELOG_MESSAGES,
  QA_STATUS_PROPERTIES,
  SUBMIT_ERROR,
} from "src/lib/constants";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "src/lib/mocks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentQAStatusEnum,
} from "src/types/globalTypes";

const Subject = ({
  onSubmit = jest.fn(),
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject {...{ onSubmit, ...props }} />
);

const qaStatus = NimbusExperimentQAStatusEnum.GREEN;
const qaComment = "Out of this world!";
const { experiment } = mockExperimentQuery("demo-slug", {
  qaStatus: NimbusExperimentQAStatusEnum.NOT_SET,
  qaComment: null,
});

describe("TableQA", () => {
  it("renders rows displaying required fields at experiment creation as expected", () => {
    render(<Subject />);

    expect(screen.queryByTestId("section-qa")).toBeInTheDocument();
    expect(screen.queryByTestId("QAEditor")).not.toBeInTheDocument();
    expect(screen.getByTestId("experiment-qa-status")).toHaveTextContent(
      "Not set",
    );
  });

  it("does not render edit button when publish status is in review", async () => {
    const publishStatus = NimbusExperimentPublishStatusEnum.REVIEW;
    render(<Subject {...{ publishStatus }} />);

    expect(screen.queryByTestId("section-qa")).toBeInTheDocument();
    expect(screen.queryByTestId("QAEditor")).not.toBeInTheDocument();
    expect(screen.queryByTestId("edit-qa-status")).not.toBeInTheDocument();
  });

  it("renders 'QA status' row as expected with status set", () => {
    render(<Subject {...{ qaStatus }} />);
    expect(screen.getByTestId("experiment-qa-status")).toHaveTextContent(
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
    );
  });

  it("renders 'QA comment' row as expected with comment set", () => {
    render(<Subject {...{ qaComment }} />);
    expect(screen.getByTestId("qa-comment")).toHaveTextContent(qaComment);
  });

  it("does not render 'QA comment' row with no comment set", () => {
    render(<Subject {...{ qaStatus }} />);
    expect(screen.queryByTestId("qa-comment")).not.toBeInTheDocument();
  });
});

describe("QAEditor", () => {
  it("appears when showEditor is true", () => {
    render(<Subject showEditor />);
    expect(screen.queryByTestId("section-qa")).not.toBeInTheDocument();
    expect(screen.queryByTestId("QAEditor")).toBeInTheDocument();
  });

  it("renders as expected with content", async () => {
    render(
      <Subject
        {...{
          showEditor: true,
          qaStatus,
          qaComment,
        }}
      />,
    );
    expect(screen.queryByTestId("QAEditor")).toBeInTheDocument();
    expect(screen.getByText("Save")).not.toBeDisabled();
    expect(screen.getByText("Cancel")).not.toBeDisabled();

    const qaStatusField = await screen.findByTestId("qa-status-section");
    expect(qaStatusField).toBeInTheDocument();
    expect(qaStatusField).toHaveTextContent(
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
    );

    const qaCommentField = await screen.findByTestId("qa-comment-section");
    expect(qaCommentField).toBeInTheDocument();
    expect(qaCommentField).toHaveTextContent(qaComment);
  });

  it("disables buttons when loading", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          isLoading: true,
          qaStatus,
        }}
      />,
    );
    expect(screen.getByText("Save")).toBeDisabled();
    expect(screen.getByText("Cancel")).toBeDisabled();
    await act(async () => {
      fireEvent.submit(screen.getByTestId("FormQA"));
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits form data when save is clicked", async () => {
    const expected = {
      qaStatus: qaStatus,
      qaComment: qaComment,
    };

    const onSubmit = jest.fn();
    const { container } = render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          qaStatus,
          qaComment,
        }}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    const result = onSubmit.mock.calls[0][0];
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());

    expect(result).toEqual(expected);
    expect(result.qaStatus).toEqual(qaStatus);
  });

  it("updates qa status and saves as expected", async () => {
    const onSubmit = jest.fn();
    const expectedStatus = NimbusExperimentQAStatusEnum.NOT_SET;
    render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
        }}
      />,
    );

    const select = await screen.findByTestId("qa-status");
    expect(select).toHaveTextContent("Not set");
    fireEvent.change(select, {
      target: { value: expectedStatus },
    });

    const status = await screen.findByTestId("qa-status");
    expect(status).toBeInTheDocument();
    expect((status as HTMLInputElement).value).toEqual(expectedStatus);

    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    const result = onSubmit.mock.calls[0][0];

    expect(onSubmit).toHaveBeenCalled();
    expect(result.qaStatus).toBeTruthy();
    expect(result.qaStatus).toEqual(expectedStatus);
  });

  it("updates qa comment and saves as expected", async () => {
    const onSubmit = jest.fn();
    const expectedComment = "What a lovely cat you have";
    render(
      <Subject
        {...{
          onSubmit,
          qaStatus,
          showEditor: true,
        }}
      />,
    );

    const textArea = await screen.findByTestId("qaComment");
    fireEvent.change(textArea, {
      target: { value: expectedComment },
    });

    expect((textArea as HTMLInputElement).value).toEqual(expectedComment);

    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    const result = onSubmit.mock.calls[0][0];

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
    expect(result.qaComment).toEqual(expectedComment);
    expect(result.qaStatus).toEqual(qaStatus);
  });

  it("hides the editor when cancel is clicked", async () => {
    const setShowEditor = jest.fn();
    render(
      <Subject
        {...{
          setShowEditor,
          showEditor: true,
          qaStatus,
          qaComment,
        }}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByText("Cancel"));
    });
    expect(setShowEditor).toHaveBeenCalledWith(false);
  });
});

describe("useQA hook", () => {
  const submitData = {
    qaStatus: NimbusExperimentQAStatusEnum.GREEN,
  };
  const mutationVariables = {
    id: experiment.id,
    qaStatus: submitData.qaStatus,
    qaComment: null,
    changelogMessage: CHANGELOG_MESSAGES.UPDATED_QA_STATUS,
  };
  let refetch = jest.fn();

  beforeEach(() => {
    refetch = jest.fn();
  });

  it("returns expected initial props", () => {
    const { result } = setupTestHook({ refetch });
    const props = result.current;
    expect(props).toMatchObject({
      id: experiment.id,
      qaStatus: experiment.qaStatus,
      qaComment: experiment.qaComment,
      showEditor: false,
      isLoading: false,
      submitErrors: {},
      isServerValid: true,
    });
    const functionNames: (keyof UseQAResult)[] = [
      "onSubmit",
      "setShowEditor",
      "setSubmitErrors",
    ];
    for (const name of functionNames) {
      expect(typeof props[name]).toEqual("function");
    }
  });

  it("performs an update mutation as expected on submit", async () => {
    const { result } = setupTestHook({
      refetch,
      mocks: [
        mockExperimentMutation(
          UPDATE_EXPERIMENT_MUTATION,
          mutationVariables,
          "updateExperiment",
          { experiment: mutationVariables },
        ),
      ],
    });
    await hookAct(async () => {
      await result.current.setShowEditor(true);
    });
    await hookAct(async () => {
      await result.current.onSubmit(submitData);
    });
    expect(refetch).toHaveBeenCalled();
    assertHookSteps(
      result,
      ["isLoading", "isServerValid", "submitErrors", "showEditor"],
      [
        [false, true, {}, false],
        [false, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, false],
        [false, true, {}, false],
      ],
    );
  });

  it("handles submit errors on submit", async () => {
    const mocks = [
      mockExperimentMutation(
        UPDATE_EXPERIMENT_MUTATION,
        mutationVariables,
        "updateExperiment",
        { experiment: mutationVariables },
      ),
    ];
    const submitErrors = {
      "*": ["Oh no! Bad server!"],
      qa_status: ["Too many bad vibes!"],
      qa_comment: ["Gotta improve the vibes"],
    };
    mocks[0].result.data.updateExperiment.message = submitErrors;
    const refetch = jest.fn();
    const { result } = setupTestHook({ refetch, mocks });
    await hookAct(async () => {
      await result.current.setShowEditor(true);
    });
    await hookAct(async () => {
      await result.current.onSubmit(submitData);
    });
    expect(refetch).not.toHaveBeenCalled();
    assertHookSteps(
      result,
      ["isLoading", "isServerValid", "submitErrors", "showEditor"],
      [
        [false, true, {}, false],
        [false, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, false, {}, true],
        [false, false, {}, true],
        [false, false, submitErrors, true],
      ],
    );
  });

  it("handles exceptions on submit", async () => {
    const mocks = [
      mockExperimentMutation(
        UPDATE_EXPERIMENT_MUTATION,
        mutationVariables,
        "updateExperiment",
        { experiment: mutationVariables },
      ),
    ];
    mocks[0].result.errors = [new Error("OOPSIE")];
    const { result } = setupTestHook({ refetch, mocks });
    await hookAct(async () => {
      await result.current.setShowEditor(true);
    });
    await hookAct(async () => {
      await result.current.onSubmit(submitData);
    });
    expect(refetch).not.toHaveBeenCalled();
    assertHookSteps(
      result,
      ["isLoading", "isServerValid", "submitErrors", "showEditor"],
      [
        [false, true, {}, false],
        [false, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, false, {}, true],
        [false, false, {}, true],
        [false, false, { "*": SUBMIT_ERROR }, true],
      ],
    );
  });

  it("handles invalid server data on submit", async () => {
    const mocks = [
      mockExperimentMutation(
        UPDATE_EXPERIMENT_MUTATION,
        mutationVariables,
        "updateExperiment",
        { experiment: mutationVariables },
      ),
    ];
    // @ts-ignore intentionally broken type
    delete mocks[0].result.data;
    const { result } = setupTestHook({ refetch, mocks });
    await hookAct(async () => {
      await result.current.setShowEditor(true);
    });
    await hookAct(async () => {
      await result.current.onSubmit(submitData);
    });
    expect(refetch).not.toHaveBeenCalled();
    assertHookSteps(
      result,
      ["isLoading", "isServerValid", "submitErrors", "showEditor"],
      [
        [false, true, {}, false],
        [false, true, {}, true],
        [true, true, {}, true],
        [true, true, {}, true],
        [true, false, {}, true],
        [false, false, {}, true],
        [false, false, { "*": SUBMIT_ERROR }, true],
      ],
    );
  });

  function assertHookSteps(
    result: HookRenderResult<UseQAResult>,
    expectedStepKeys: (keyof UseQAResult)[],
    expectedSteps: any[],
  ) {
    for (let stepIdx = 0; stepIdx < expectedSteps.length; stepIdx++) {
      expect(result.all[stepIdx]).not.toBeInstanceOf(Error);
      const props = result.all[stepIdx] as UseQAResult;
      // Zip together the expected step keys with values into expected object
      const expected = expectedStepKeys.reduce(
        (acc, key, idx) => ({ ...acc, [key]: expectedSteps[stepIdx][idx] }),
        {},
      );
      expect(props).toMatchObject(expected);
    }
  }
});

const defaultMockExperiment = experiment;
const setupTestHook = ({
  experiment = defaultMockExperiment,
  refetch = jest.fn(),
  mocks = [],
}: {
  experiment?: getExperiment_experimentBySlug;
  refetch?: () => Promise<void>;
  mocks?: MockedResponse[];
}) => {
  return renderHook(() => useQA(experiment, refetch), {
    wrapper,
    initialProps: { mocks },
  });
};

const wrapper = ({
  mocks = [],
  children,
}: {
  mocks?: MockedResponse[];
  children?: React.ReactNode;
}) => (
  <MockedCache {...{ mocks }}>{children as React.ReactElement}</MockedCache>
);
