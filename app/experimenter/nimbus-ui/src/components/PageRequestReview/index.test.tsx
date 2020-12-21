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
import fetchMock from "jest-fetch-mock";
import PageRequestReview from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { createMutationMock } from "./mocks";
import { navigate } from "@reach/router";
import { BASE_PATH } from "../../lib/constants";

jest.mock("@reach/router", () => ({
  ...jest.requireActual("@reach/router"),
  navigate: jest.fn(),
}));

describe("PageRequestReview", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
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

  it("redirects to the first edit page containing missing fields if the experiment status is draft and its not ready for review", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
      readyForReview: {
        __typename: "NimbusReadyForReviewType",
        ready: false,
        message: {
          // This field exists on the Audience page
          firefox_min_version: ["This field may not be null."],
        },
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        navigate,
      ).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/edit/audience?show-errors`,
        { replace: true },
      );
    });
  });

  it("redirects to the overview edit page if the experiment status is draft and its not ready for review, and for some reason invalid pages is empty", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
      readyForReview: {
        __typename: "NimbusReadyForReviewType",
        ready: false,
        message: {},
      },
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        navigate,
      ).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/edit/overview?show-errors`,
        { replace: true },
      );
    });
  });

  it("redirects to the design page if the experiment status is live", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/design`,
        {
          replace: true,
        },
      );
    });
  });

  it("redirects to the design page if the experiment status is complete", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/design`,
        {
          replace: true,
        },
      );
    });
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
