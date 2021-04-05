/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import FormApproveOrReject from "./FormApproveOrReject";
import FormRejectReason from "./FormRejectReason";
import FormRemoteSettingsPending from "./FormRemoteSettingsPending";
import { mockChangelog, SubjectChangeApprovalOperations } from "./mocks";

const SubjectChangeApprovalOperationsWithActions = ({
  rejectChange = action("rejectChange"),
  approveChange = action("approveChange"),
  startRemoteSettingsApproval = action("startRemoteSettingsApproval"),
  ...props
}: React.ComponentProps<typeof SubjectChangeApprovalOperations>) => (
  <SubjectChangeApprovalOperations
    {...{
      rejectChange,
      approveChange,
      startRemoteSettingsApproval,
      ...props,
    }}
  />
);

storiesOf("components/ChangeApprovalOperations", module)
  .addDecorator(withLinks)
  .addDecorator((story) => <div className="p-5">{story()}</div>)
  .add("review not requested", () => (
    <SubjectChangeApprovalOperationsWithActions />
  ))
  .add("review requested, user can review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        canReview: true,
      }}
    />
  ))
  .add("review pending in Remote Rettings, user can review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        canReview: true,
      }}
    />
  ))
  .add("review timed out in Remote Settings, user can review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        timeoutEvent: mockChangelog("ghi@mozilla.com"),
        canReview: true,
      }}
    />
  ))
  .add("review requested, user cannot review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        canReview: false,
      }}
    />
  ))
  .add("review pending in Remote Settings, user cannot review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        canReview: false,
      }}
    />
  ))
  .add("review timed out in Remote Settings, user cannot review", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        timeoutEvent: mockChangelog("ghi@mozilla.com"),
        canReview: false,
      }}
    />
  ))
  .add("review rejected in experimenter or remote settings", () => (
    <SubjectChangeApprovalOperationsWithActions
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        rejectionEvent: mockChangelog(
          "ghi@mozilla.com",
          "It's bad. Just start over.",
        ),
        canReview: true,
      }}
    />
  ));

storiesOf("components/ChangeApprovalOperations/forms", module)
  .addDecorator(withLinks)
  .addDecorator((story) => <div className="p-5">{story()}</div>)
  .add("FormApproveOrReject", () => (
    <FormApproveOrReject
      {...{
        actionDescription: "froblulate",
        isLoading: false,
        reviewRequestEvent: mockChangelog(),
        timeoutEvent: mockChangelog("ghi@mozilla.com"),
        onApprove: action("approve"),
        onReject: action("reject"),
      }}
    />
  ))
  .add("FormRejectReason", () => (
    <FormRejectReason
      {...{
        isLoading: false,
        onSubmit: action("submit"),
        onCancel: action("cancel"),
      }}
    />
  ))
  .add("FormRemoteSettingsPending", () => (
    <FormRemoteSettingsPending
      {...{
        isLoading: false,
        onConfirm: action("confirm"),
      }}
    />
  ));
