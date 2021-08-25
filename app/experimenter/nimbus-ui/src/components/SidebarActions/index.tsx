/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import ReactTooltip from "react-tooltip";
import { useChangeOperationMutation } from "../../hooks";
import { ReactComponent as Info } from "../../images/info.svg";
import { ARCHIVE_DISABLED, CHANGELOG_MESSAGES } from "../../lib/constants";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { LinkNav } from "../LinkNav";
import { ReactComponent as CloneIcon } from "./clone.svg";
import CloneDialog, { CloneParams } from "./CloneDialog";
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
    isLoading,
    callbacks: [onUpdateArchived],
  } = useChangeOperationMutation(experiment, refetch, {
    isArchived: !experiment.isArchived,
    changelogMessage: !experiment.isArchived
      ? CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT
      : CHANGELOG_MESSAGES.UNARCHIVING_EXPERIMENT,
  });

  const disabled = !experiment.canArchive || isLoading;

  const [cloneShowDialog, cloneSetShowDialog] = useState(false);
  const cloneOnShow = () => cloneSetShowDialog(true);
  const cloneOnCancel = () => cloneSetShowDialog(false);

  // TODO: EXP-1138 replace this next block when clone mutation is available
  const canClone = true;
  const cloneIsLoading = false;
  const cloneIsServerValid = true;
  const cloneSubmitErrors = {};
  /* istanbul ignore next EXP-1138 - pending mutation implementation */
  const cloneSetSubmitErrors = () => {};
  /* istanbul ignore next EXP-1138 - pending mutation implementation */
  const cloneOnSave = (data: CloneParams) => {
    cloneOnCancel();
    window.alert("Sorry, experiment cloning is not yet implemented.");
  };

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
          disabled={!canClone || isLoading}
          testid="action-clone"
          onClick={cloneOnShow}
        >
          <CloneIcon className="sidebar-icon" />
          Clone
        </LinkNav>
        <CloneDialog
          {...{
            experiment,
            show: cloneShowDialog,
            onCancel: cloneOnCancel,
            onSave: cloneOnSave,
            isLoading: cloneIsLoading,
            isServerValid: cloneIsServerValid,
            submitErrors: cloneSubmitErrors,
            setSubmitErrors: cloneSetSubmitErrors,
          }}
        />
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
          <TrashIcon className="sidebar-icon" />
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
        </LinkNav>
      </div>
    </div>
  );
};

export default SidebarActions;
