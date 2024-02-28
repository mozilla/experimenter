/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import React, { useState } from "react";
import { Card } from "react-bootstrap";
import Alert from "react-bootstrap/Alert";
import NotSet from "src/components/NotSet";
import TableSignoff from "src/components/PageSummary/TableSignoff";
import Takeaways, { useTakeaways } from "src/components/PageSummary/Takeaways";
import PreviewURL from "src/components/PreviewURL";
import CancelReview from "src/components/Summary/CancelReview";
import EndEnrollment from "src/components/Summary/EndEnrollment";
import EndExperiment from "src/components/Summary/EndExperiment";
import RequestLiveUpdate from "src/components/Summary/RequestLiveUpdate";
import TableAudience from "src/components/Summary/TableAudience";
import TableBranches from "src/components/Summary/TableBranches";
import TableOverview from "src/components/Summary/TableOverview";
import TableQA from "src/components/Summary/TableQA";
import useQA from "src/components/Summary/TableQA/useQA";
import TableRiskMitigation from "src/components/Summary/TableRiskMitigation";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { useChangeOperationMutation } from "src/hooks";
import { CHANGELOG_MESSAGES } from "src/lib/constants";
import { getStatus } from "src/lib/experiment";
import { ConfigOptions, getConfigLabel } from "src/lib/getConfigLabel";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

type SummaryProps = {
  experiment: getExperiment_experimentBySlug;
  refetch?: () => Promise<unknown>;
};

const Summary = ({ experiment, refetch }: SummaryProps) => {
  const takeawaysProps = useTakeaways(experiment, refetch);
  const qaProps = useQA(experiment, refetch);
  const status = getStatus(experiment);
  const [legalSignoff, setLegalSignoff] = useState(
    experiment.legalSignoff || false,
  );
  const [qaSignoff, setQaSignoff] = useState(experiment.qaSignoff || false);
  const [vpSignoff, setVpSignoff] = useState(experiment.vpSignoff || false);
  const [updateExperiment] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const handleLegalSignoffChange = (value: boolean) => {
    setLegalSignoff(value);
    updateExperimentSignoff(value, qaSignoff, vpSignoff);
  };

  const handleQaSignoffChange = (value: boolean) => {
    setQaSignoff(value);
    updateExperimentSignoff(legalSignoff, value, vpSignoff);
  };

  const handleVpSignoffChange = (value: boolean) => {
    setVpSignoff(value);
    updateExperimentSignoff(legalSignoff, qaSignoff, value);
  };
  const updateExperimentSignoff = async (
    legal: boolean,
    qa: boolean,
    vp: boolean,
  ) => {
    try {
      const result = await updateExperiment({
        variables: {
          input: {
            id: experiment.id,
            legalSignoff: legal,
            qaSignoff: qa,
            vpSignoff: vp,
            changelogMessage: CHANGELOG_MESSAGES.UPDATE_SIGNOFF,
          },
        },
      });
    } catch (error) {
      // Handle error
      console.error("Error updating sign-off values:", error);
    }
  };
  const shouldDisableUpdateButton =
    !status.dirty || status.review || status.approved || status.waiting;

  const {
    isLoading,
    submitError,
    callbacks: [
      onConfirmEndClicked,
      onConfirmEndEnrollmentClicked,
      onConfirmCancelReviewClicked,
      onRequestUpdateClicked,
    ],
  } = useChangeOperationMutation(
    experiment,
    refetch,
    {
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.COMPLETE,
      isEnrollmentPaused: true,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
    },
    {
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      isEnrollmentPaused: experiment.isWeb ? false : true,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
    },
    {
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
      changelogMessage: CHANGELOG_MESSAGES.CANCEL_REVIEW,
      statusNext: null,
      isEnrollmentPaused:
        experiment.statusNext === NimbusExperimentStatusEnum.COMPLETE
          ? experiment.isEnrollmentPaused
          : false,
    },
    {
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      status: NimbusExperimentStatusEnum.LIVE,
      statusNext: NimbusExperimentStatusEnum.LIVE,
      changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_UPDATE,
    },
  );

  return (
    <div data-testid="summary" className="mb-5">
      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      {!status.complete && (
        <Card className="border-left-0 border-right-0 border-bottom-0">
          <Card.Header as="h5">Actions</Card.Header>
          <Card.Body>
            {experiment.isRollout && status.live && (
              <RequestLiveUpdate
                {...{
                  isLoading,
                  onSubmit: onRequestUpdateClicked,
                  disable: shouldDisableUpdateButton,
                }}
              />
            )}

            {status.live &&
              !status.approved &&
              !status.review &&
              (status.idle || status.dirty) &&
              !status.pauseRequested &&
              !experiment.isEnrollmentPaused &&
              !experiment.isRollout && (
                <EndEnrollment
                  {...{ isLoading, onSubmit: onConfirmEndEnrollmentClicked }}
                />
              )}

            {status.live &&
              !status.review &&
              !status.endRequested &&
              (status.idle || status.dirty) && (
                <EndExperiment
                  {...{
                    isLoading,
                    onSubmit: onConfirmEndClicked,
                    isRollout: !!experiment.isRollout, // Use double negation (!!) to coerce experiment to boolean value
                  }}
                />
              )}
            {status.review && (
              <CancelReview
                {...{ isLoading, onSubmit: onConfirmCancelReviewClicked }}
              />
            )}
            {(status.live || status.preview) && (
              <PreviewURL {...experiment} status={status} />
            )}

            {status.draft && !status.review ? "No Action needed" : ""}
          </Card.Body>
        </Card>
      )}
      {!status.launched && (
        <Card className="mb-4 border-left-0 border-right-0 border-bottom-0">
          <Card.Header as="h5" data-testid="summary-page-signoff-not-launched">
            Recommended actions before launch
          </Card.Header>

          <TableSignoff
            signoffRecommendations={experiment.signoffRecommendations}
            legalSignoff={legalSignoff}
            qaSignoff={qaSignoff}
            vpSignoff={vpSignoff}
            onLegalSignoffChange={handleLegalSignoffChange}
            onQaSignoffChange={handleQaSignoffChange}
            onVpSignoffChange={handleVpSignoffChange}
          />
        </Card>
      )}
      {status.complete && <Takeaways {...takeawaysProps} />}
      <TableOverview {...{ experiment }} />
      <TableRiskMitigation {...{ experiment }} />

      <TableAudience {...{ experiment }} />
      {status.launched && (
        <Card className="border-left-0 border-right-0 border-bottom-0">
          <Card.Header as="h5" data-testid="summary-page-signoff-launched">
            Actions that were recommended before launch
          </Card.Header>

          <TableSignoff
            signoffRecommendations={experiment.signoffRecommendations}
            legalSignoff={legalSignoff}
            qaSignoff={qaSignoff}
            vpSignoff={vpSignoff}
            onLegalSignoffChange={handleLegalSignoffChange}
            onQaSignoffChange={handleQaSignoffChange}
            onVpSignoffChange={handleVpSignoffChange}
          />
        </Card>
      )}

      {/* Branches title is inside its table */}
      <TableBranches {...{ experiment }} />
      <TableQA {...qaProps} />
    </div>
  );
};

export const displayConfigLabelOrNotSet = (
  value: string | null,
  options: ConfigOptions,
) => {
  if (!value) return <NotSet />;
  return getConfigLabel(value, options);
};

export default Summary;
