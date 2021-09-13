/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import ReactTooltip from "react-tooltip";
import { useChangeOperationMutation } from "../../hooks";
import { ReactComponent as BookIcon } from "../../images/book.svg";
import { ReactComponent as FeedbackIcon } from "../../images/chat-square-text.svg";
import { ReactComponent as Info } from "../../images/info.svg";
import { ReactComponent as SlackIcon } from "../../images/slack.svg";
import {
  ARCHIVE_DISABLED,
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
} from "../../lib/constants";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import CloneDialog, { useCloneDialog } from "../CloneDialog";
import LinkExternal from "../LinkExternal";
import { LinkNav } from "../LinkNav";
import { ReactComponent as CloneIcon } from "./clone.svg";
import { ReactComponent as TrashIcon } from "./trash.svg";

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
    isLoading: archiveIsLoading,
    callbacks: [onUpdateArchived],
  } = useChangeOperationMutation(experiment, refetch, {
    isArchived: !experiment.isArchived,
    changelogMessage: !experiment.isArchived
      ? CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT
      : CHANGELOG_MESSAGES.UNARCHIVING_EXPERIMENT,
  });

  const archiveDisabled = !experiment.canArchive;

  const cloneDialogProps = useCloneDialog(experiment);

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
          key="sidebar-actions-clone"
          disabled={cloneDialogProps.disabled}
          testid="action-clone"
          onClick={cloneDialogProps.onShow}
        >
          <CloneIcon className="sidebar-icon" />
          Clone
        </LinkNav>
        <CloneDialog {...cloneDialogProps} />
      </div>
      <div>
        <LinkNav
          useButton
          key="sidebar-actions-archive"
          route={`${experiment.slug}/#`}
          testid="action-archive"
          onClick={onUpdateArchived}
          {...{ disabled: archiveDisabled || archiveIsLoading }}
        >
          <TrashIcon className="sidebar-icon" />
          {experiment.isArchived ? "Unarchive" : "Archive"}
          {archiveDisabled && (
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
        </LinkNav>
        <div className="edit-divider position-relative small my-3">
          <span className="position-relative bg-light pl-1 pr-2 text-muted">
            Links
          </span>
        </div>
        <LinkExternal
          className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          href={EXTERNAL_URLS.EXPERIMENTER_DOCUMENTATION}
        >
          <BookIcon className="mr-2" /> Experimenter Documentation
        </LinkExternal>
        <LinkExternal
          className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          href={EXTERNAL_URLS.ASK_EXPERIMENTER_SLACK}
        >
          <SlackIcon className="mr-2" /> #ask-experimenter
        </LinkExternal>
        <LinkExternal
          className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          href={EXTERNAL_URLS.FEEDBACK}
        >
          <FeedbackIcon className="mr-2" /> Feedback
        </LinkExternal>
      </div>
    </div>
  );
};

export default SidebarActions;
