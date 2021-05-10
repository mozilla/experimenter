/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useRef, useState } from "react";
import { Table } from "react-bootstrap";
import Alert from "react-bootstrap/Alert";
import { useChangeOperationMutation } from "../../hooks";
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
}: PageRequestReviewProps) => {
  const { kintoAdminUrl } = useConfig();
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [showLaunchToReview, setShowLaunchToReview] = useState(false);

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
    currentExperiment,
    refetchReview,
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

  return (
    <AppLayoutWithExperiment
      title="Review &amp; Launch"
      testId="PageRequestReview"
      {...{ polling }}
      redirect={({ status, review }) => {
        if (review && status.draft && !review.ready) {
          // If the experiment is not ready to be reviewed, let's send them to
          // the first page we know needs fixing up, with field errors displayed
          return `edit/${review.invalidPages[0] || "overview"}?show-errors`;
        }

        if (status.launched) {
          // Return to the experiment root/summary page
          return "";
        }
      }}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;
        const status = getStatus(experiment);
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

            {(status.draft || status.preview) && (
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
                        onLaunchWithoutPreview: () =>
                          setShowLaunchToReview(true),
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
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
