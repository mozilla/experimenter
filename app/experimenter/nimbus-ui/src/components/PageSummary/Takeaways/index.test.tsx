/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { fireEvent, render, screen } from "@testing-library/react";
import {
  act as hookAct,
  renderHook,
  RenderResult as HookRenderResult,
} from "@testing-library/react-hooks";
import React from "react";
import { act } from "react-dom/test-utils";
import { useTakeaways, UseTakeawaysResult } from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../../lib/constants";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { NimbusExperimentConclusionRecommendationEnum } from "../../../types/globalTypes";
import { Subject as BaseSubject } from "./mocks";

const { experiment } = mockExperimentQuery("demo-slug", {
  takeawaysSummary: "old content",
  conclusionRecommendation: NimbusExperimentConclusionRecommendationEnum.RERUN,
});

const Subject = ({
  onSubmit = jest.fn(),
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject {...{ onSubmit, ...props }} />
);

const takeawaysSummary = "sample *exciting* content";
const conclusionRecommendation =
  NimbusExperimentConclusionRecommendationEnum.CHANGE_COURSE;
const expectedConclusionRecommendationLabel = "Change course";

describe("Takeaways", () => {
  it("renders as expected when blank", () => {
    render(<Subject />);
    expect(screen.queryByTestId("Takeaways")).toBeInTheDocument();
    expect(screen.queryByTestId("TakeawaysEditor")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("conclusion-recommendation-status"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("edit-takeaways")).toBeInTheDocument();
    expect(
      screen.queryByTestId("takeaways-summary-rendered"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("not-set")).toBeInTheDocument();
  });

  it("renders as expected with content", () => {
    render(<Subject {...{ takeawaysSummary, conclusionRecommendation }} />);
    expect(screen.queryByTestId("Takeaways")).toBeInTheDocument();
    expect(screen.queryByTestId("TakeawaysEditor")).not.toBeInTheDocument();
    expect(
      screen.getByTestId("conclusion-recommendation-status"),
    ).toHaveTextContent(expectedConclusionRecommendationLabel);
    expect(screen.getByTestId("takeaways-summary-rendered")).toContainHTML(
      "<p>sample <em>exciting</em> content</p>",
    );
    expect(screen.queryByTestId("edit-takeaways")).toBeInTheDocument();
    expect(screen.queryByTestId("not-set")).not.toBeInTheDocument();
  });

  it("renders takeaways without edit button when experiment is archived", () => {
    render(
      <Subject
        {...{ takeawaysSummary, conclusionRecommendation, isArchived: true }}
      />,
    );
    expect(screen.queryByTestId("Takeaways")).toBeInTheDocument();
    expect(screen.queryByTestId("TakeawaysEditor")).not.toBeInTheDocument();
    expect(
      screen.getByTestId("conclusion-recommendation-status"),
    ).toHaveTextContent(expectedConclusionRecommendationLabel);
    expect(screen.getByTestId("takeaways-summary-rendered")).toContainHTML(
      "<p>sample <em>exciting</em> content</p>",
    );
    expect(screen.queryByTestId("edit-takeaways")).not.toBeInTheDocument();
    expect(screen.queryByTestId("not-set")).not.toBeInTheDocument();
  });

  it("sets showEditor to true when the edit button is clicked", () => {
    const setShowEditor = jest.fn();
    render(
      <Subject
        {...{ setShowEditor, takeawaysSummary, conclusionRecommendation }}
      />,
    );
    const editButton = screen.getByTestId("edit-takeaways");
    fireEvent.click(editButton);
    expect(setShowEditor).toHaveBeenCalledWith(true);
  });
});

describe("TakeawaysEditor", () => {
  it("appears when showEditor is true", () => {
    render(<Subject showEditor />);
    expect(screen.queryByTestId("Takeaways")).not.toBeInTheDocument();
    expect(screen.queryByTestId("TakeawaysEditor")).toBeInTheDocument();
  });

  it("renders as expected with content", () => {
    render(
      <Subject
        {...{ showEditor: true, takeawaysSummary, conclusionRecommendation }}
      />,
    );
    expect(screen.queryByTestId("TakeawaysEditor")).toBeInTheDocument();
    expect(screen.getByText("Save")).not.toBeDisabled();
    expect(screen.getByText("Cancel")).not.toBeDisabled();
    const editorForm = screen.getByTestId("FormTakeaways");
    expect(editorForm).toHaveFormValues({
      takeawaysSummary,
      conclusionRecommendation,
    });
  });

  it("disables buttons when loading", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          isLoading: true,
          takeawaysSummary,
          conclusionRecommendation,
        }}
      />,
    );
    expect(screen.getByText("Save")).toBeDisabled();
    expect(screen.getByText("Cancel")).toBeDisabled();
    await act(async () => {
      fireEvent.submit(screen.getByTestId("FormTakeaways"));
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits form data when save is clicked", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          takeawaysSummary,
          conclusionRecommendation,
        }}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    expect(onSubmit).toHaveBeenCalled();
  });

  it("hides the editor when cancel is clicked", async () => {
    const setShowEditor = jest.fn();
    render(
      <Subject
        {...{
          setShowEditor,
          showEditor: true,
          takeawaysSummary,
          conclusionRecommendation,
        }}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByText("Cancel"));
    });
    expect(setShowEditor).toHaveBeenCalledWith(false);
  });

  it("displays server submission errors", async () => {
    const submitErrors = {
      "*": ["Meteor fell on the server!"],
      takeaways_summary: ["Too many mentions of chickens!"],
      conclusion_recommendation: ["'Ship it' is an invalid recommendation."],
    };
    const { container } = render(
      <Subject
        {...{
          showEditor: true,
          takeawaysSummary,
          conclusionRecommendation,
          isServerValid: false,
          submitErrors,
        }}
      />,
    );
    expect(screen.getByTestId("submit-error")).toHaveTextContent(
      submitErrors["*"][0],
    );
    expect(
      container.querySelector('.invalid-feedback[data-for="takeawaysSummary"]'),
    ).toHaveTextContent(submitErrors.takeaways_summary[0]);
    expect(
      container.querySelector(
        '.invalid-feedback[data-for="conclusionRecommendation"]',
      ),
    ).toHaveTextContent(submitErrors.conclusion_recommendation[0]);
  });
});

describe("useTakeaways", () => {
  const submitData = {
    takeawaysSummary: "super exciting results",
    conclusionRecommendation: NimbusExperimentConclusionRecommendationEnum.STOP,
  };
  const mutationVariables = {
    id: experiment.id,
    takeawaysSummary: submitData.takeawaysSummary,
    conclusionRecommendation: submitData.conclusionRecommendation,
    changelogMessage: CHANGELOG_MESSAGES.UPDATED_TAKEAWAYS,
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
      takeawaysSummary: experiment.takeawaysSummary,
      conclusionRecommendation: experiment.conclusionRecommendation,
      showEditor: false,
      isLoading: false,
      submitErrors: {},
      isServerValid: true,
    });
    const functionNames: (keyof UseTakeawaysResult)[] = [
      "onSubmit",
      "setShowEditor",
      "setSubmitErrors",
    ];
    for (const name of functionNames) {
      expect(typeof props[name]).toEqual("function");
    }
  });

  it("performs a mutation as expected via onSubmit", async () => {
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

  it("handles submit error feedback as expected via onSubmit", async () => {
    const mocks = [
      mockExperimentMutation(
        UPDATE_EXPERIMENT_MUTATION,
        mutationVariables,
        "updateExperiment",
        { experiment: mutationVariables },
      ),
    ];
    const submitErrors = {
      "*": ["Meteor fell on the server!"],
      takeaways_summary: ["Too many mentions of chickens!"],
      conclusion_recommendation: ["'Ship it' is an invalid recommendation."],
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

  it("handles exceptions as expected via onSubmit", async () => {
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

  it("handles invalid server data as expected via onSubmit", async () => {
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
    result: HookRenderResult<UseTakeawaysResult>,
    expectedStepKeys: (keyof UseTakeawaysResult)[],
    expectedSteps: any[],
  ) {
    for (let stepIdx = 0; stepIdx < expectedSteps.length; stepIdx++) {
      expect(result.all[stepIdx]).not.toBeInstanceOf(Error);
      const props = result.all[stepIdx] as UseTakeawaysResult;
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
  return renderHook(() => useTakeaways(experiment, refetch), {
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
