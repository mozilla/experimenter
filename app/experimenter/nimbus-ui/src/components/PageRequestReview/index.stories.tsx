/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageRequestReview from ".";
import { humanDate } from "../../lib/dateUtils";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import FormApproveConfirm from "./FormApproveConfirm";
import FormApproveOrRejectLaunch from "./FormApproveOrRejectLaunch";
import FormRejectReason from "./FormRejectReason";
import {
  mock,
  Subject,
  SubjectDraftStatusOperations,
  SubjectEXP1055,
} from "./mocks";

const mockRejectFeedback = {
  rejectedByUser: "example@mozilla.com",
  rejectDate: humanDate("2020-11-28T14:52:44.704811+00:00"),
  rejectReason: "It's bad. Just start over.",
};

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("preview status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("review status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("non-reviewable", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("error", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ));

storiesOf("pages/RequestReview/EXP-1055", module)
  .addDecorator(withLinks)
  .add("draft status", () => {
    return <Subject />;
  })
  .add("review not requested", () => <SubjectEXP1055 />)
  .add("review requested, user has reviewer role", () => (
    <SubjectEXP1055
      {...{
        isLaunchRequested: true,
        currentUserCanApprove: true,
        currentUser: "abc@mozilla.com",
        launchRequestedByUsername: "def@mozilla.com",
      }}
    />
  ))
  .add(
    "review approved in experimenter, not yet approved in remote settings, user has reviewer role",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  )
  .add("review requested, user does not have reviewer role", () => (
    <SubjectEXP1055
      {...{ isLaunchRequested: true, currentUserCanApprove: false }}
    />
  ))
  .add(
    "review requested, user has reviewer role, but user requested this review",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: false,
          currentUser: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter, not yet approved in remote settings, user does not have reviewer role",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: false,
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter, not yet approved in remote settings, user has reviewer role, but user requested this review",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user has reviewer role, but user has requested this review",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user has reviewer role, but user did not request this review",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user does not have reviewer role, but user did not request this review",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: false,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter but request timed out in Remote Settings, user has reviewer role",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: true,
          rsRequestTimedOut: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter but request timed out in Remote Settings, user does not have reviewer role",
    () => (
      <SubjectEXP1055
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: false,
          rsRequestTimedOut: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  );

const SubjectDraftStatusOperationsWithActions = ({
  rejectExperimentLaunch = action("rejectExperimentLaunch"),
  approveExperimentLaunch = action("approveExperimentLaunch"),
  confirmExperimentLaunchApproval = action("confirmExperimentLaunchApproval"),
  onLaunchClicked = action("onLaunchClicked"),
  onLaunchToPreviewClicked = action("onLaunchToPreviewClicked"),
  ...props
}: React.ComponentProps<typeof SubjectDraftStatusOperations>) => (
  <SubjectDraftStatusOperations
    {...{
      rejectExperimentLaunch,
      approveExperimentLaunch,
      confirmExperimentLaunchApproval,
      onLaunchClicked,
      onLaunchToPreviewClicked,
      ...props,
    }}
  />
);

storiesOf("pages/RequestReview/EXP-1055/DraftStatusOperations", module)
  .addDecorator(withLinks)
  .addDecorator((story) => <div className="p-5">{story()}</div>)
  .add("review not requested", () => (
    <SubjectDraftStatusOperationsWithActions />
  ))
  .add("review requested, user has reviewer role", () => (
    <SubjectDraftStatusOperationsWithActions
      {...{
        isLaunchRequested: true,
        currentUserCanApprove: true,
        currentUsername: "abc@mozilla.com",
        launchRequestedByUsername: "def@mozilla.com",
      }}
    />
  ))
  .add(
    "review approved in experimenter, not yet approved in remote settings, user has reviewer role",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  )
  .add("review requested, user does not have reviewer role", () => (
    <SubjectDraftStatusOperationsWithActions
      {...{ isLaunchRequested: true, currentUserCanApprove: false }}
    />
  ))
  .add(
    "review requested, user has reviewer role, but user requested this review",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter, not yet approved in remote settings, user does not have reviewer role",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: false,
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter, not yet approved in remote settings, user has reviewer role, but user requested this review",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: true,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user has reviewer role, but user has requested this review",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "abc@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user has reviewer role, but user did not request this review",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review rejected in experimenter or remote settings, user does not have reviewer role, but user did not request this review",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          isLaunchApproved: false,
          currentUserCanApprove: false,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
          rejectFeedback: mockRejectFeedback,
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter but request timed out in Remote Settings, user has reviewer role",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: true,
          rsRequestTimedOut: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  )
  .add(
    "review approved in experimenter but request timed out in Remote Settings, user does not have reviewer role",
    () => (
      <SubjectDraftStatusOperationsWithActions
        {...{
          isLaunchRequested: true,
          currentUserCanApprove: false,
          rsRequestTimedOut: true,
          currentUsername: "abc@mozilla.com",
          launchRequestedByUsername: "def@mozilla.com",
        }}
      />
    ),
  );

storiesOf("pages/RequestReview/EXP-1055/forms", module)
  .addDecorator(withLinks)
  .addDecorator((story) => <div className="p-5">{story()}</div>)
  .add("FormApproveOrRejectLaunch", () => (
    <FormApproveOrRejectLaunch
      {...{
        launchRequestedByUsername: "jdoe@mozilla.com",
        isLoading: false,
        onApprove: action("approve"),
        onReject: action("reject"),
      }}
    />
  ))
  .add("FormRejectReason", () => (
    <FormRejectReason
      {...{
        isLoading: false,
        isServerValid: true,
        submitErrors: {},
        setSubmitErrors: () => {},
        onSubmit: action("submit"),
        onCancel: action("cancel"),
      }}
    />
  ))
  .add("FormApproveConfirm", () => (
    <FormApproveConfirm
      {...{
        isLoading: false,
        onConfirm: action("confirm"),
      }}
    />
  ));
