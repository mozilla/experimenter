/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import {
  act as hookAct,
  renderHook,
  RenderResult as HookRenderResult,
} from "@testing-library/react-hooks";
import React from "react";
import { act } from "react-dom/test-utils";
import {
  useTakeaways,
  UseTakeawaysResult,
} from "src/components/PageSummary/Takeaways";
import { Subject as BaseSubject } from "src/components/PageSummary/Takeaways/mocks";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "src/lib/constants";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "src/lib/mocks";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentConclusionRecommendationEnum } from "src/types/globalTypes";

const { experiment } = mockExperimentQuery("demo-slug", {
  takeawaysSummary: "old content",
  takeawaysQbrLearning: true,
  takeawaysMetricGain: false,
  takeawaysGainAmount: null,
  conclusionRecommendation: NimbusExperimentConclusionRecommendationEnum.RERUN,
});

const Subject = ({
  onSubmit = jest.fn(),
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject {...{ onSubmit, ...props }} />
);

const takeawaysGainAmount = "sick gains all around";
const takeawaysMetricGain = false;
const takeawaysQbrLearning = true;
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
    expect(
      within(screen.getByTestId("summary")).queryByTestId("not-set"),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId("takeaways-gain-amount-rendered"),
    ).not.toBeInTheDocument();
    expect(
      within(screen.getByTestId("gain-amount")).queryByTestId("not-set"),
    ).toBeInTheDocument();
  });

  it("renders as expected with content", () => {
    render(
      <Subject
        {...{
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
          conclusionRecommendation,
        }}
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
    expect(screen.queryByTestId("edit-takeaways")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("gain-amount")).queryByTestId("not-set"),
    ).not.toBeInTheDocument();
  });

  it("renders takeaways without edit button when experiment is archived", () => {
    render(
      <Subject
        {...{
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
          conclusionRecommendation,
          isArchived: true,
        }}
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
        {...{
          setShowEditor,
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
          conclusionRecommendation,
        }}
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
        {...{
          showEditor: true,
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
          conclusionRecommendation,
        }}
      />,
    );
    expect(screen.queryByTestId("TakeawaysEditor")).toBeInTheDocument();
    expect(screen.getByText("Save")).not.toBeDisabled();
    expect(screen.getByText("Cancel")).not.toBeDisabled();
    const editorForm = screen.getByTestId("FormTakeaways");
    expect(editorForm).toHaveFormValues({
      takeawaysSummary,
      takeawaysGainAmount,
      conclusionRecommendation,
    });
    expect(screen.queryByTestId("takeaways-qbr")).toBeInTheDocument();
    expect(screen.queryByTestId("takeaways-metric")).toBeInTheDocument();
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
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
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
    const expected = {
      takeawaysGainAmount: takeawaysGainAmount,
      takeawaysMetricGain: takeawaysMetricGain,
      takeawaysQbrLearning: takeawaysQbrLearning,
      takeawaysSummary: takeawaysSummary,
      conclusionRecommendation: conclusionRecommendation,
    };
    const onSubmit = jest.fn();
    const { container } = render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          takeawaysSummary,
          takeawaysGainAmount,
          takeawaysMetricGain,
          takeawaysQbrLearning,
          conclusionRecommendation,
        }}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });

    const result = onSubmit.mock.calls[0][0];

    await waitFor(() => expect(onSubmit).toHaveBeenCalled());

    expect(result).toEqual(expected);
    expect(result.takeawaysGainAmount).toEqual(takeawaysGainAmount);
    expect(result.takeawaysMetricGain).toEqual(takeawaysMetricGain);
    expect(result.takeawaysQbrLearning).toEqual(takeawaysQbrLearning);
  });

  it("updates takeaways checkboxes and saves as expected", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        {...{
          onSubmit,
          showEditor: true,
          takeawaysSummary,
          takeawaysGainAmount,
          takeawaysMetricGain: false,
          takeawaysQbrLearning: false,
          conclusionRecommendation,
        }}
      />,
    );
    expect(screen.getByTestId("takeawaysQbrLearning")).not.toBeChecked();

    await act(async () => {
      fireEvent.click(screen.getByTestId("takeawaysQbrLearning"));
    });

    expect(screen.getByTestId("takeawaysQbrLearning")).toBeChecked();

    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    const result1 = onSubmit.mock.calls[0][0];

    expect(onSubmit).toHaveBeenCalled();
    expect(result1.takeawaysQbrLearning).toBeTruthy();
    expect(result1.takeawaysQbrLearning).toEqual(true);

    expect(screen.getByTestId("takeawaysMetricGain")).not.toBeChecked();

    await act(async () => {
      fireEvent.click(screen.getByTestId("takeawaysMetricGain"));
    });

    expect(screen.getByTestId("takeawaysMetricGain")).toBeChecked();

    await act(async () => {
      fireEvent.click(screen.getByText("Save"));
    });
    const result2 = onSubmit.mock.calls[1][0];

    expect(onSubmit).toHaveBeenCalledTimes(2);
    expect(result2.takeawaysMetricGain).toBeTruthy();
    expect(result2.takeawaysMetricGain).toEqual(true);
  });

  it("hides the editor when cancel is clicked", async () => {
    const setShowEditor = jest.fn();
    render(
      <Subject
        {...{
          setShowEditor,
          showEditor: true,
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysGainAmount,
          takeawaysMetricGain,
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
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
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
    takeawaysQbrLearning: true,
    takeawaysMetricGain: false,
    takeawaysGainAmount: "lots of sick gains",
    conclusionRecommendation: NimbusExperimentConclusionRecommendationEnum.STOP,
  };
  const mutationVariables = {
    id: experiment.id,
    takeawaysSummary: submitData.takeawaysSummary,
    takeawaysQbrLearning: submitData.takeawaysQbrLearning,
    takeawaysMetricGain: submitData.takeawaysMetricGain,
    takeawaysGainAmount: submitData.takeawaysGainAmount,
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
      takeawaysGainAmount: experiment.takeawaysGainAmount,
      takeawaysMetricGain: experiment.takeawaysMetricGain,
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
