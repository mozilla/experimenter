/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, screen } from "@testing-library/dom";
import { render, waitFor } from "@testing-library/react";
import React from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { Subject } from "./mocks";

const { mock: queryMock, experiment } = mockExperimentQuery();
const createMutationMock = () =>
  mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id: experiment.id,
      changelogMessage: CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT,
      isArchived: true,
      archiveReason: "foo",
    },
    "updateExperiment",
  );

describe("ArchiveDialogue", () => {
  it("can submit the archiving request", async () => {
    const refetch = jest.fn();
    const onClose = jest.fn();
    render(<Subject {...{ refetch, onClose }} />);
    fireEvent.change(screen.getByPlaceholderText("reason", { exact: false }), {
      target: { value: "foo" },
    });
    fireEvent.click(screen.getByText("Save"));
    await waitFor(() => {
      expect(refetch).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("can cancel the archiving request", async () => {
    const onClose = jest.fn();
    render(<Subject {...{ onClose }} />);
    fireEvent.click(screen.getByText("Cancel"));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("handles form submission with bad server data", async () => {
    const mutationMock = createMutationMock();
    // @ts-ignore - intentionally breaking this type for error handling
    delete mutationMock.result.data.updateExperiment;
    render(
      <Subject
        experimentId={experiment.id!}
        mocks={[queryMock, mutationMock]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("reason", { exact: false }), {
      target: { value: "foo" },
    });
    fireEvent.click(await screen.findByText("Save"));
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        SUBMIT_ERROR,
      ),
    );
  });

  it("handles form submission with server API error", async () => {
    const mutationMock = createMutationMock();
    mutationMock.result.errors = [new Error("an error")];
    render(
      <Subject
        experimentId={experiment.id!}
        mocks={[queryMock, mutationMock]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText("reason", { exact: false }), {
      target: { value: "foo" },
    });
    fireEvent.click(await screen.findByText("Save"));
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        SUBMIT_ERROR,
      ),
    );
  });
});
