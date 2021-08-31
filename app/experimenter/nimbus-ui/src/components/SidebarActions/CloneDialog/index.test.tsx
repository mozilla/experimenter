/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import {
  createHistory,
  createMemorySource,
  History,
  HistorySource,
} from "@reach/router";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import CloneDialog, { useCloneDialog } from ".";
import { CLONE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { BASE_PATH, SUBMIT_ERROR } from "../../../lib/constants";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { MemoryHistorySource } from "../../../lib/types";

describe("CloneDialog", () => {
  it("renders, cancels, and saves as expected", async () => {
    const onSave = jest.fn();
    const onCancel = jest.fn();

    render(<Subject {...{ onSave, onCancel }} />);

    const nameField = screen.getByLabelText("Public name") as HTMLInputElement;

    await waitFor(() => {
      expect(screen.queryByText("Save")).toBeInTheDocument();
      expect(screen.queryByText("Saving")).not.toBeInTheDocument();
      expect(nameField.value).toEqual(`${mockExperiment!.name} Copy`);
    });

    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalled();

    const saveButton = screen.getByText("Save");

    act(() => void fireEvent.change(nameField, { target: { value: "Oh hi" } }));
    await waitFor(() => expect(saveButton).not.toBeDisabled());

    fireEvent.click(saveButton);
    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
      expect(onSave.mock.calls[0][0]).toEqual({ name: "Oh hi" });
    });
  });

  it("indicates when cloning is in progress", async () => {
    render(<Subject isLoading={true} />);
    await waitFor(() => {
      expect(screen.queryByText("Save")).not.toBeInTheDocument();
      expect(screen.queryByText("Saving")).toBeInTheDocument();
      expect(screen.queryByText("Saving")).toBeDisabled();
    });
  });

  it("keeps the slug in sync with the name field", async () => {
    render(<Subject />);
    const nameField = screen.getByLabelText("Public name");
    const slugField = screen.getByTestId("SlugTextControl") as HTMLInputElement;
    for (const [nameValue, expectedSlug] of [
      ["Hello", "hello"],
      ["Hello world", "hello-world"],
    ]) {
      fireEvent.change(nameField, { target: { value: nameValue } });
      await waitFor(() => {
        expect(slugField.value).toEqual(expectedSlug);
      });
    }
  });
});

describe("CloneDialog with useCloneDialog props", () => {
  let mockHistory: History;
  let mockHistorySource: MemoryHistorySource;
  let navigateSpy: jest.SpyInstance<Promise<void>, any>;

  beforeEach(() => {
    mockHistorySource = createMemorySource(
      "/xyzzy/edit",
    ) as MemoryHistorySource;
    mockHistory = createHistory(mockHistorySource);
    navigateSpy = jest.spyOn(mockHistory, "navigate");
  });

  it("reveals dialog with onShow, hides with onCancel calls", async () => {
    render(<SubjectWithHook />);
    const showButton = screen.getByTestId("show-dialog");

    expect(screen.queryByTestId("CloneDialog")).not.toBeInTheDocument();

    act(() => void fireEvent.click(showButton));
    await waitFor(
      () =>
        void expect(screen.queryByTestId("CloneDialog")).toBeInTheDocument(),
    );

    act(() => void fireEvent.click(screen.getByText("Cancel")));
    await waitFor(
      () =>
        void expect(
          screen.queryByTestId("CloneDialog"),
        ).not.toBeInTheDocument(),
    );
  });

  const expectedName = "Hello world";
  const expectedSlug = "hello-world";

  const mockCloneMutation = () => ({
    request: {
      query: CLONE_EXPERIMENT_MUTATION,
      variables: {
        input: {
          parentSlug: mockExperiment.slug,
          name: expectedName,
        },
      },
    },
    result: {
      data: {
        cloneExperiment: {
          message: "success" as string | Record<string, any>,
          nimbusExperiment: {
            slug: expectedSlug,
          } as Record<string, string> | undefined,
        },
      },
    },
  });

  const baseCloneTest = async (
    mocks?: MockedResponse<Record<string, any>>[],
  ) => {
    render(<SubjectWithHook {...{ mocks, mockHistorySource, mockHistory }} />);

    const showButton = screen.getByTestId("show-dialog");
    act(() => void fireEvent.click(showButton));
    await waitFor(
      () =>
        void expect(screen.queryByTestId("CloneDialog")).toBeInTheDocument(),
    );

    const nameField = screen.getByLabelText("Public name");
    const slugField = screen.getByTestId("SlugTextControl") as HTMLInputElement;
    const saveButton = screen.getByText("Save");

    fireEvent.change(nameField!, { target: { value: expectedName } });
    await waitFor(() => {
      expect(slugField.value).toEqual(expectedSlug);
    });

    fireEvent.click(saveButton);
    await waitFor(
      () =>
        void expect(
          screen.queryByTestId("loading-dialog"),
        ).not.toBeInTheDocument(),
    );
  };

  it("submits the clone request as expected", async () => {
    await baseCloneTest([mockCloneMutation()]);
    await waitFor(
      () =>
        void expect(
          screen.queryByTestId("CloneDialog"),
        ).not.toBeInTheDocument(),
    );
    expect(navigateSpy).toHaveBeenCalledWith(`${BASE_PATH}/${expectedSlug}`);
  });

  it("handles malformed data from server", async () => {
    const mutation = mockCloneMutation();
    // @ts-ignore breaking the type on purpose
    delete mutation.result.data.cloneExperiment;

    await baseCloneTest([mutation]);

    await waitFor(
      () => void expect(screen.queryByText(SUBMIT_ERROR)).toBeInTheDocument(),
    );
    expect(screen.queryByTestId("CloneDialog")).toBeInTheDocument();
    expect(navigateSpy).not.toHaveBeenCalledWith(
      `${BASE_PATH}/${expectedSlug}`,
    );
  });

  it("handles errors reported from the server", async () => {
    const expectedSubmitError = "This name is garbage";
    const mutation = mockCloneMutation();
    mutation.result.data.cloneExperiment.message = {
      name: expectedSubmitError,
    };

    await baseCloneTest([mutation]);

    await waitFor(() =>
      expect(
        screen.getByTestId("CloneDialog").querySelector(".invalid-feedback"),
      ).toHaveTextContent(expectedSubmitError),
    );
    expect(screen.queryByTestId("CloneDialog")).toBeInTheDocument();
    expect(navigateSpy).not.toHaveBeenCalledWith(
      `${BASE_PATH}/${expectedSlug}`,
    );
  });
});

type SubjectProps = Partial<React.ComponentProps<typeof CloneDialog>>;

const { experiment: mockExperiment } = mockExperimentQuery("my-special-slug");

const Subject = ({
  show = true,
  experiment = mockExperiment,
  isLoading = false,
  isServerValid = true,
  submitErrors = {},
  setSubmitErrors = () => {},
  onCancel = () => {},
  onSave = () => {},
}: SubjectProps) => (
  <CloneDialog
    {...{
      show,
      experiment,
      isLoading,
      isServerValid,
      submitErrors,
      setSubmitErrors,
      onCancel,
      onSave,
    }}
  />
);

const SubjectWithHook = ({
  mocks,
  mockHistorySource,
  mockHistory,
  ...innerProps
}: {
  mocks?: MockedResponse<Record<string, any>>[];
  mockHistorySource?: HistorySource;
  mockHistory?: History;
} & Pick<SubjectProps, "experiment">) => (
  <RouterSlugProvider {...{ mocks, mockHistorySource, mockHistory }}>
    <SubjectWithHookInner {...innerProps} />
  </RouterSlugProvider>
);

const SubjectWithHookInner = ({
  experiment = mockExperiment,
}: Pick<SubjectProps, "experiment">) => {
  const cloneDialogProps = useCloneDialog(experiment);
  const { onShow, isLoading } = cloneDialogProps;
  return (
    <div>
      <button data-testid="show-dialog" onClick={onShow}>
        Show
      </button>
      {isLoading && <div data-testid="loading-dialog">Loading...</div>}
      <CloneDialog {...cloneDialogProps} />
    </div>
  );
};
