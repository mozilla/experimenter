/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import { mockExperiment, mockExperimentMutation } from "../../lib/mocks";
import { Subject } from "./mocks";

describe("SidebarActions", () => {
  it("renders sidebar actions content", () => {
    render(<Subject />);
    expect(screen.getByTestId("SidebarActions")).toBeInTheDocument();
  });

  it("renders a disabled archive button for unarchived experiment", () => {
    render(<Subject experiment={{ isArchived: false, canArchive: false }} />);
    expect(screen.getByTestId("action-archive")).toHaveClass("text-muted");
    expect(screen.getByTestId("action-archive")).toHaveTextContent("Archive");
    expect(screen.getByTestId("tooltip-archived-disabled")).toBeInTheDocument();
  });

  it("renders an enabled archive button for unarchived experiment", () => {
    render(<Subject experiment={{ isArchived: false, canArchive: true }} />);
    expect(screen.getByTestId("action-archive").tagName).toEqual("BUTTON");
    expect(screen.getByTestId("action-archive")).toHaveTextContent("Archive");
    expect(
      screen.queryByTestId("tooltip-archived-disabled"),
    ).not.toBeInTheDocument();
  });
  it("renders a disabled unarchive button for archived experiment", () => {
    render(<Subject experiment={{ isArchived: true, canArchive: false }} />);
    expect(screen.getByTestId("action-archive")).toHaveClass("text-muted");
    expect(screen.getByTestId("action-archive")).toHaveTextContent("Unarchive");
    expect(screen.getByTestId("tooltip-archived-disabled")).toBeInTheDocument();
  });

  it("renders an enabled archive button for unarchived experiment", () => {
    render(<Subject experiment={{ isArchived: true, canArchive: true }} />);
    expect(screen.getByTestId("action-archive").tagName).toEqual("BUTTON");
    expect(screen.getByTestId("action-archive")).toHaveTextContent("Unarchive");
    expect(
      screen.queryByTestId("tooltip-archived-disabled"),
    ).not.toBeInTheDocument();
  });
  it("calls update archive mutation when archive button is clicked", async () => {
    const experiment = mockExperiment({ isArchived: false, canArchive: true });
    const refetch = jest.fn();
    const mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
      {
        id: experiment.id,
        isArchived: true,
        changelogMessage: CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT,
      },
      "updateExperiment",
      {
        message: "success",
      },
    );

    render(<Subject {...{ experiment, refetch }} mocks={[mutationMock]} />);

    const archiveButton = await screen.findByTestId("action-archive");

    fireEvent.click(archiveButton);
    await waitFor(() => {
      expect(refetch).toHaveBeenCalled();
    });
  });
  it("calls update archive mutation when unarchive button is clicked", async () => {
    const experiment = mockExperiment({ isArchived: true, canArchive: true });
    const refetch = jest.fn();
    const mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
      {
        id: experiment.id,
        isArchived: false,
        changelogMessage: CHANGELOG_MESSAGES.UNARCHIVING_EXPERIMENT,
      },
      "updateExperiment",
      {
        message: "success",
      },
    );

    render(<Subject {...{ experiment, refetch }} mocks={[mutationMock]} />);

    const archiveButton = await screen.findByTestId("action-archive");

    fireEvent.click(archiveButton);
    await waitFor(() => {
      expect(refetch).toHaveBeenCalled();
    });
  });

  it("manages revealing and hiding the clone experiment dialog", async () => {
    const experiment = mockExperiment({ isArchived: false, canArchive: true });

    render(<Subject {...{ experiment }} />);

    const cloneButton = await screen.findByTestId("action-clone");

    expect(screen.queryByTestId("CloneDialog")).not.toBeInTheDocument();

    fireEvent.click(cloneButton);
    await waitFor(() => {
      expect(screen.queryByTestId("CloneDialog")).toBeInTheDocument();
    });

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);
    await waitFor(() => {
      expect(screen.queryByTestId("CloneDialog")).not.toBeInTheDocument();
    });
  });
});
