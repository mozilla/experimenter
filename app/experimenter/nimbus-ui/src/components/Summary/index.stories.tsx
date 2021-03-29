/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { storiesOf } from "@storybook/react";
import React from "react";
import Summary from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import AppLayout from "../AppLayout";
import { mockChangelog } from "../ChangeApprovalOperations/mocks";

storiesOf("components/Summary", module)
  .add("draft status", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    return <Subject {...{ experiment }} />;
  })
  .add("non-draft status", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.WAITING,
    });
    return <Subject {...{ experiment }} />;
  })
  .add("live status", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    const mutationMock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
      {
        id: experiment.id!,
      },
      "endExperiment",
    );
    return <Subject {...{ experiment, mocks: [mutationMock] }} />;
  })
  .add("end requested", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEndRequested: true,
    });
    return <Subject {...{ experiment }} />;
  })
  .add("enrollment active", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEnrollmentPaused: false,
    });
    return <Subject {...{ experiment }} />;
  })
  .add("enrollment ended", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      enrollmentEndDate: new Date().toISOString(),
    });
    return <Subject {...{ experiment }} />;
  })
  .add("enrollment ended + end requested", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEndRequested: true,
      enrollmentEndDate: new Date().toISOString(),
    });
    return <Subject {...{ experiment }} />;
  })
  .add("no branches", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      referenceBranch: null,
      treatmentBranches: null,
    });
    return <Subject {...{ experiment }} />;
  });

const Subject = ({
  experiment,
  mocks = [],
}: {
  experiment: getExperiment_experimentBySlug;
  mocks?: MockedResponse<Record<string, any>>[];
}) => (
  <AppLayout>
    <RouterSlugProvider {...{ mocks }}>
      <Summary {...{ experiment }} />
    </RouterSlugProvider>
  </AppLayout>
);

const SubjectEXP1143 = ({
  ...props
}: Partial<React.ComponentProps<typeof Summary>>) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatus.LIVE,
  });
  const mutationMock = mockExperimentMutation(
    END_EXPERIMENT_MUTATION,
    {
      id: experiment.id!,
    },
    "endExperiment",
  );
  const mocks = [mutationMock];
  return (
    <AppLayout>
      <RouterSlugProvider {...{ mocks }}>
        <Summary {...{ experiment, ...props }} />
      </RouterSlugProvider>
    </AppLayout>
  );
};

storiesOf("components/Summary/EXP-1143; end experiment review flow", module)
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
          "Not ready to end yet, having too much fun.",
        ),
        canReview: true,
      }}
    />
  ));
