/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import { Table } from "react-bootstrap";
import Alert from "react-bootstrap/Alert";
import { useChangeOperationMutation, useReviewCheck } from "../../hooks";
import { useConfig } from "../../hooks/useConfig";
import { CHANGELOG_MESSAGES, EXTERNAL_URLS } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ChangeApprovalOperations from "../ChangeApprovalOperations";
import LinkExternal from "../LinkExternal";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageRequestReview = ({
  /* istanbul ignore next - only used in tests & stories */
  polling = true,
}: PageRequestReviewProps) => (
  <AppLayoutWithExperiment
    title="Review &amp; Launch"
    testId="PageRequestReview"
    {...{ polling }}
    redirect={({ status }) => {
      if (status.launched) {
        // Return to the experiment root/summary page
        return "";
      }
    }}
  >
    {({ experiment, refetch }) => <PageContent {...{ experiment, refetch }} />}
  </AppLayoutWithExperiment>
);

const PageContent: React.FC<{
  experiment: getExperiment_experimentBySlug;
  refetch: () => void;
}> = ({ experiment, refetch }) => {
  const { kintoAdminUrl } = useConfig();
  const [showLaunchToReview, setShowLaunchToReview] = useState(false);
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);

  const status = getStatus(experiment);
  const startRemoteSettingsApproval = async () => {
    window.open(kintoAdminUrl!, "_blank");
  };

  const {
    isLoading,
    submitError,
    callbacks: [
      onLaunchToPreviewClicked,
      onBackToDraftClicked,
      onLaunchClicked,
      onReviewApprovedClicked,
      onReviewRejectedClicked,
    ],
  } = useChangeOperationMutation(
    experiment,
    refetch,
    {
      status: NimbusExperimentStatus.PREVIEW,
      changelogMessage: CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      changelogMessage: CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
      changelogMessage: CHANGELOG_MESSAGES.REVIEW_APPROVED,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.IDLE,
    },
  );

  const {
    publishStatus,
    canReview,
    reviewRequest: reviewRequestEvent,
    rejection: rejectionEvent,
    timeout: timeoutEvent,
  } = experiment;

  return (
    <>
      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {(status.draft || status.preview) && invalidPages.length > 0 ? (
        <Alert variant="warning">
          Before this experiment can be reviewed or launched, all required
          fields must be completed. Fields on the <InvalidPagesList />{" "}
          {invalidPages.length === 1 ? "page" : "pages"} are missing details.
        </Alert>
      ) : (
        <ChangeApprovalOperations
          {...{
            actionDescription: "launch",
            isLoading,
            publishStatus,
            canReview: !!canReview,
            reviewRequestEvent,
            rejectionEvent,
            timeoutEvent,
            rejectChange: onReviewRejectedClicked,
            approveChange: onReviewApprovedClicked,
            startRemoteSettingsApproval,
          }}
        >
          {status.draft &&
            (showLaunchToReview ? (
              <FormLaunchDraftToReview
                {...{
                  isLoading,
                  onSubmit: onLaunchClicked,
                  onCancel: () => setShowLaunchToReview(false),
                  onLaunchToPreview: onLaunchToPreviewClicked,
                }}
              />
            ) : (
              <FormLaunchDraftToPreview
                {...{
                  isLoading,
                  onSubmit: onLaunchToPreviewClicked,
                  onLaunchWithoutPreview: () => setShowLaunchToReview(true),
                }}
              />
            ))}

          {status.preview && status.idle && (
            <FormLaunchPreviewToReview
              {...{
                isLoading,
                onSubmit: onLaunchClicked,
                onBackToDraft: onBackToDraftClicked,
              }}
            />
          )}
        </ChangeApprovalOperations>
      )}

      <h3 className="h5 mb-3">Recommended actions before launch</h3>
      <Table bordered data-testid="table-signoff" className="mb-4">
        <tbody>
          <tr data-testid="table-signoff-qa">
            <td>
              <strong>QA Sign-off</strong>
            </td>
            <td>
              {experiment.signoffRecommendations?.qaSignoff && (
                <span className="text-success">Recommended: </span>
              )}
              Describe what they should do.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_QA}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
          <tr data-testid="table-signoff-vp">
            <td>
              <strong>VP Sign-off</strong>
            </td>
            <td>
              {experiment.signoffRecommendations?.vpSignoff && (
                <span className="text-success">Recommended: </span>
              )}
              Describe what they should do.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_VP}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
          <tr data-testid="table-signoff-legal">
            <td>
              <strong>Legal Sign-off</strong>
            </td>
            <td>
              {experiment.signoffRecommendations?.legalSignoff && (
                <span className="text-success">Recommended: </span>
              )}
              Describe what they should do.{" "}
              <LinkExternal href={EXTERNAL_URLS.SIGNOFF_LEGAL}>
                Learn More
              </LinkExternal>
            </td>
          </tr>
        </tbody>
      </Table>

      <Summary {...{ experiment }} />
    </>
  );
};

export default PageRequestReview;
