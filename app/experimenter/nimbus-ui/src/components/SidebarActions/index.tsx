/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import ReactTooltip from "react-tooltip";
import { useChangeOperationMutation } from "../../hooks";
import { ReactComponent as Info } from "../../images/info.svg";
import { ARCHIVE_DISABLED, CHANGELOG_MESSAGES } from "../../lib/constants";
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

  const disabled = !experiment.canArchive || isLoading;
  return (
    <div data-testid={"SidebarActions"}>
      <div className="edit-divider position-relative small my-2">
        <span className="position-relative bg-light pl-1 pr-2 text-muted">
          Actions
        </span>
      </div>
      <div>
        <LinkNav
          useButton
          key="sidebar-actions-archive"
          route={`${experiment.slug}/#`}
          testid="action-archive"
          onClick={onUpdateArchived}
          {...{ disabled }}
        >
          <Trash className="sidebar-icon" />
          <div>
            <p className="m-0">
              {experiment.isArchived ? "Unarchive" : "Archive"}
              {disabled && (
                <>
                  <Info
                    data-tip={ARCHIVE_DISABLED}
                    data-testid="tooltip-archived-disabled"
                    width="20"
                    height="20"
                    className="ml-1 text-muted"
                  />
                  <ReactTooltip />
                </>
              )}
            </p>
          </div>
        </LinkNav>
      </div>
    </div>
  );
};

export default SidebarActions;
