/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import { useChangeOperationMutation } from "../../hooks";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { LinkNav } from "../LinkNav";
import { ReactComponent as Trash } from "./trash.svg";

type SidebarModifyExperimentProps = {
  testid?: string;
  experiment: getExperiment_experimentBySlug;
  refetch: () => Promise<any>;
} & RouteComponentProps;

export const SidebarActions = ({
  experiment,
  refetch,
}: SidebarModifyExperimentProps) => {
  const {
    isLoading,
    callbacks: [onUpdateArchived],
  } = useChangeOperationMutation(experiment, refetch, {
    isArchived: !experiment.isArchived,
    changelogMessage: !experiment.isArchived
      ? CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT
      : CHANGELOG_MESSAGES.UNARCHIVING_EXPERIMENT,
  });

  return (
    <div data-testid={"SidebarActions"}>
      <p className="edit-divider position-relative small my-2">
        <span className="position-relative bg-light pl-1 pr-2 text-muted">
          Actions
        </span>
      </p>
      <p>
        <LinkNav
          useButton
          key="sidebar-actions-archive"
          disabled={!experiment.canArchive || isLoading}
          testid="action-archive"
          onClick={onUpdateArchived}
        >
          <Trash className="sidebar-icon" />
          {experiment.isArchived
            ? "Unarchive Experiment"
            : "Archive Experiment"}
        </LinkNav>
      </p>
    </div>
  );
};

export default SidebarActions;
