/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { Subject } from "src/components/SidebarActions/mocks";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { CHANGELOG_MESSAGES } from "src/lib/constants";
import { mockExperiment, mockExperimentMutation } from "src/lib/mocks";
import {
  NimbusExperimentDocumentationLinkEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

describe("SidebarActions", () => {
  it("renders sidebar actions content", () => {
    render(<Subject />);
    expect(screen.getByTestId("SidebarActions")).toBeInTheDocument();
  });

  it("displays expected links", async () => {
    render(
      <Subject
        {...{
          experiment: {
            slug: "demo-slug",
            status: NimbusExperimentStatusEnum.LIVE,
            showResultsUrl: true,
            riskMitigationLink: "https://mozilla.org",
            documentationLinks: [
              {
                title: NimbusExperimentDocumentationLinkEnum.DESIGN_DOC,
                link: "https://mozilla.org",
              },
              {
                title: NimbusExperimentDocumentationLinkEnum.DS_JIRA,
                link: "https://twitter.com",
              },
            ],
          },
        }}
      />,
    );
    expect(screen.getAllByTestId("experiment-additional-link")).toHaveLength(2);
    expect(screen.queryByTestId("link-monitoring-dashboard")).toHaveAttribute(
      "href",
      expect.stringContaining("https://mozilla.cloud.looker.com"),
    );
    expect(screen.queryByTestId("link-external-results")).toHaveAttribute(
      "href",
      "https://protosaur.dev/partybal/demo_slug.html",
    );
    expect(
      screen.queryByTestId("risk-mitigation-checklist-link"),
    ).toHaveAttribute("href", expect.stringContaining("https://mozilla.org"));
  });

  it("displays opmon link when rollout and launched", async () => {
    render(
      <Subject
        {...{
          experiment: {
            slug: "demo-slug-1",
            status: NimbusExperimentStatusEnum.LIVE,
            isRollout: true,
            rolloutMonitoringDashboardUrl: "https://mozilla.org/linklinklink",
          },
        }}
      />,
    );
    expect(
      screen.queryByTestId("link-rollout-monitoring-dashboard"),
    ).toHaveAttribute(
      "href",
      expect.stringContaining("https://mozilla.org/linklinklink"),
    );
  });

  it("does not render risk mitigation link when not set", () => {
    render(<Subject {...{ experiment: { riskMitigationLink: undefined } }} />);
    expect(
      screen.queryByTestId("risk-mitigation-checklist-link"),
    ).not.toBeInTheDocument();
  });

  it("does not render monitoring dashboard URL if experiment has not been launched", () => {
    render(
      <Subject
        experiment={{
          status: NimbusExperimentStatusEnum.DRAFT,
        }}
      />,
    );
    expect(
      screen.queryByTestId("link-monitoring-dashboard"),
    ).not.toBeInTheDocument();
  });

  it("does not render opmon URL if experiment has not been launched and not rollout", () => {
    render(
      <Subject
        experiment={{
          status: NimbusExperimentStatusEnum.DRAFT,
          isRollout: false,
        }}
      />,
    );
    expect(
      screen.queryByTestId("link-rollout-monitoring-dashboard"),
    ).not.toBeInTheDocument();
  });

  it("does not render additional links where there are none", () => {
    render(
      <Subject
        experiment={{
          documentationLinks: [],
        }}
      />,
    );
    expect(
      screen.queryByTestId("experiment-additional-links"),
    ).not.toBeInTheDocument();
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

    // Issue #6303: Expect disable button during loading, but not the tooltip
    await waitFor(() => {
      expect(screen.getByTestId("action-archive")).toHaveClass("text-muted");
      expect(
        screen.queryByTestId("tooltip-archived-disabled"),
      ).not.toBeInTheDocument();
    });

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

  it("scrolls to json when preview recipe json button is clicked", async () => {
    const experiment = mockExperiment({ isArchived: false, canArchive: true });
    const refetch = jest.fn();
    render(<Subject {...{ experiment, refetch }} />);

    const jsonButton = await screen.findByTestId("button-recipe-json");

    fireEvent.click(jsonButton);

    await waitFor(() => {
      expect(
        screen.queryByTestId("button-recipe-json"),
      ).not.toBeInTheDocument();
    });
  });
});
