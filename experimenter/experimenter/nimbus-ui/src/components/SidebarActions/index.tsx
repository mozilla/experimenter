/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link, RouteComponentProps } from "@reach/router";
import React, { useEffect } from "react";
import ReactTooltip from "react-tooltip";
import { ReactComponent as CogIcon } from "src/components/AppLayoutWithSidebar/cog.svg";
import CloneDialog, { useCloneDialog } from "src/components/CloneDialog";
import LinkExternal from "src/components/LinkExternal";
import { LinkNav } from "src/components/LinkNav";
import { ReactComponent as CloneIcon } from "src/components/SidebarActions/clone.svg";
import "src/components/SidebarActions/index.scss";
import { ReactComponent as TrashIcon } from "src/components/SidebarActions/trash.svg";
import {
  useChangeOperationMutation,
  useConfig,
  useScrollToLocationHash,
} from "src/hooks";
import { ReactComponent as BookIcon } from "src/images/book.svg";
import { ReactComponent as FeedbackIcon } from "src/images/chat-square-text.svg";
import { ReactComponent as ExternalIcon } from "src/images/external.svg";
import { ReactComponent as GithubIcon } from "src/images/github.svg";
import { ReactComponent as Info } from "src/images/info.svg";
import { ReactComponent as SlackIcon } from "src/images/slack.svg";
import {
  ARCHIVE_DISABLED,
  BASE_PATH,
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
} from "src/lib/constants";
import { StatusCheck } from "src/lib/experiment";
import { AnalysisData } from "src/lib/visualization/types";
import { analysisUnavailable } from "src/lib/visualization/utils";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type SidebarModifyExperimentProps = {
  testid?: string;
  experiment: getExperiment_experimentBySlug;
  refetch: () => Promise<any>;
  status: StatusCheck;
  analysis?: AnalysisData;
} & RouteComponentProps;

export const SidebarActions = ({
  experiment,
  refetch,
  status,
  analysis,
}: SidebarModifyExperimentProps) => {
  const {
    slug,
    documentationLinks,
    monitoringDashboardUrl,
    recipeJson,
    riskMitigationLink,
  } = experiment;
  const { documentationLink: configDocumentationLinks } = useConfig();
  const scrollIntoView = useScrollToLocationHash();
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
  const rebuildToolTip = () => {
    ReactTooltip.rebuild();
  };
  useEffect(() => {
    rebuildToolTip();
  }, [archiveDisabled]);

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
            <Info
              data-tip={ARCHIVE_DISABLED}
              data-testid="tooltip-archived-disabled"
              width="20"
              height="20"
              className="ml-1 text-muted"
            >
              <ReactTooltip />
            </Info>
          )}
        </LinkNav>

        <div className="edit-divider position-relative small my-3">
          <span className="position-relative bg-light pl-1 pr-2 text-muted">
            Links
          </span>
        </div>

        {documentationLinks &&
          documentationLinks?.length > 0 &&
          documentationLinks.map((documentationLink, idx) => (
            <LinkExternal
              href={documentationLink.link}
              data-testid="experiment-additional-link"
              key={`doc-link-${idx}`}
              className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
            >
              <ExternalIcon className="sidebar-icon-external-link" />
              {
                configDocumentationLinks!.find(
                  (d) => d?.value === documentationLink.title,
                )?.label
              }
            </LinkExternal>
          ))}

        {riskMitigationLink && (
          <LinkExternal
            href={riskMitigationLink}
            data-testid="risk-mitigation-checklist-link"
            className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          >
            <ExternalIcon className="sidebar-icon-external-link" />
            Risk mitigation checklist
          </LinkExternal>
        )}

        {status.launched && (
          <LinkExternal
            href={monitoringDashboardUrl!}
            data-testid="link-monitoring-dashboard"
            className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          >
            <ExternalIcon className="sidebar-icon-external-link" />
            Live Monitoring Dashboard
          </LinkExternal>
        )}

        {status.launched && experiment.rolloutMonitoringDashboardUrl && (
          <LinkExternal
            href={experiment.rolloutMonitoringDashboardUrl!}
            data-testid="link-rollout-monitoring-dashboard"
            className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          >
            <ExternalIcon className="sidebar-icon-external-link" />
            Rollouts OpMon Dashboard
          </LinkExternal>
        )}

        {status.launched && !analysisUnavailable(analysis) && (
          <LinkExternal
            href={EXTERNAL_URLS.DETAILED_ANALYSIS_TEMPLATE(slug)}
            data-testid="link-external-results"
            className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          >
            <ExternalIcon className="sidebar-icon-external-link" />
            Detailed Analysis
          </LinkExternal>
        )}

        {recipeJson && (
          <Link
            to={`${BASE_PATH}/${slug}#recipe-json`}
            onClick={() => scrollIntoView}
            className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
            data-testid="button-recipe-json"
          >
            <CogIcon className="sidebar-icon" />
            Preview Recipe JSON
          </Link>
        )}
        <div className="edit-divider position-relative small my-3">
          <span className="position-relative bg-light pl-1 pr-2 text-muted">
            Help
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
        <LinkExternal
          className="mx-1 my-2 nav-item d-block text-dark w-100 font-weight-normal"
          href={EXTERNAL_URLS.GITHUB_TICKET}
        >
          <GithubIcon className="mr-2" /> File targeting criteria request
        </LinkExternal>
      </div>
    </div>
  );
};

export default SidebarActions;
