/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageRequestReview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { mockChangelog } from "../ChangeApprovalOperations/mocks";
import { mock, Subject, SubjectEXP1143 } from "./mocks";

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("draft status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("preview status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("preview status + approved publish status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("preview status + publish status waiting", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
      publishStatus: NimbusExperimentPublishStatus.WAITING,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("review status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("non-reviewable", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.WAITING,
    });
    return <Subject {...{ mocks: [mock] }} />;
  })
  .add("error", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ));

storiesOf(
  "pages/RequestReview/EXP-1143; end experiment review refactor",
  module,
)
  .addDecorator(withLinks)
  .add("review not requested", () => <SubjectEXP1143 />)
  .add("review requested, user can review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        canReview: true,
      }}
    />
  ))
  .add("review pending in Remote Rettings, user can review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        canReview: true,
      }}
    />
  ))
  .add("review timed out in Remote Settings, user can review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        timeoutEvent: mockChangelog("ghi@mozilla.com"),
        canReview: true,
      }}
    />
  ))
  .add("review requested, user cannot review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        canReview: false,
      }}
    />
  ))
  .add("review pending in Remote Settings, user cannot review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        canReview: false,
      }}
    />
  ))
  .add("review timed out in Remote Settings, user cannot review", () => (
    <SubjectEXP1143
      {...{
        reviewRequestEvent: mockChangelog(),
        approvalEvent: mockChangelog("def@mozilla.com"),
        timeoutEvent: mockChangelog("ghi@mozilla.com"),
        canReview: false,
      }}
    />
  ))
  .add("review rejected", () => (
    <SubjectEXP1143
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
