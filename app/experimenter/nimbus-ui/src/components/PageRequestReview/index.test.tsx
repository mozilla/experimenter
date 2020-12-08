/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import PageRequestReview from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { createMutationMock } from "./mocks";

describe("PageRequestReview", () => {
  // This component is currently set up to handle an experiment
  // that is live, accepted, and complete, and as a result also performs
  // an analysis lookup. In practice, and when EXP-497 is complete, this
  // page should not be accessed. For now I'm stubbing the console.error
  // that occurs when the analysis lookup happens.
  // TODO: EXP-497, remove branches and tests that handle locked experiment
  // state, and remove this console.error stubbing
  let origError: typeof global.console.error;

  beforeEach(() => {
    origError = global.console.error;
    global.console.error = jest.fn();
  });

  afterEach(() => {
    global.console.error = origError;
  });

  async function checkRequiredBoxes() {
    const checkboxes = screen.queryAllByTestId("required-checkbox");

    for (const checkbox of checkboxes) {
      await act(async () => void fireEvent.click(checkbox));
    }
  }

  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(() => {
      expect(screen.getByTestId("PageRequestReview")).toBeInTheDocument();
      submitButton = screen.getByText("Launch") as HTMLButtonElement;
    });
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
    await checkRequiredBoxes();
    expect(submitButton!).toBeEnabled();
    await checkRequiredBoxes();
    expect(submitButton!).toBeDisabled();
  });

  it("can submit for review", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id);

    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(
      () => (submitButton = screen.getByText("Launch") as HTMLButtonElement),
    );
    await checkRequiredBoxes();
    await act(async () => void fireEvent.click(submitButton));
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("handles submission with bad server data", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id);
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperimentStatus;
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(
      () => (submitButton = screen.getByText("Launch") as HTMLButtonElement),
    );
    await checkRequiredBoxes();
    await act(async () => void fireEvent.click(submitButton));
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toBeInTheDocument(),
    );
  });

  it("handles submission with server API error", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id);
    mutationMock.result.errors = [new Error("Boo")];
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(
      () => (submitButton = screen.getByText("Launch") as HTMLButtonElement),
    );
    await checkRequiredBoxes();
    await act(async () => void fireEvent.click(submitButton));
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toBeInTheDocument(),
    );
  });

  it("handles submission with server-side validation errors", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createMutationMock(experiment.id);
    const errorMessage =
      "Nimbus Experiments can only transition from DRAFT to REVIEW.";
    mutationMock.result.data.updateExperimentStatus.message = {
      status: [errorMessage],
    };
    render(<Subject mocks={[mock, mutationMock]} />);
    let submitButton: HTMLButtonElement;
    await waitFor(
      () => (submitButton = screen.getByText("Launch") as HTMLButtonElement),
    );
    await checkRequiredBoxes();
    await act(async () => void fireEvent.click(submitButton));
    await waitFor(() => {
      expect(screen.getByTestId("submit-error")).toBeInTheDocument();
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        errorMessage,
      );
    });
  });

  it("will not allow submitting if already in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("will not allow submitting if already accepted", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("cant-review-label")).toBeInTheDocument(),
    );
  });

  it("will not allow submitting if already complete", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("cant-review-label")).toBeInTheDocument(),
    );
  });
});

const Subject = ({
  mocks = [],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageRequestReview />
  </RouterSlugProvider>
);
