/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageRequestReview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import FormApproveConfirm from "./FormApproveConfirm";
import FormApproveOrRejectLaunch from "./FormApproveOrRejectLaunch";
import FormRejectReason from "./FormRejectReason";
import { mock, Subject } from "./mocks";
import FormApproveConfirm from "./FormApproveConfirm";
import FormApproveOrRejectLaunch from "./FormApproveOrRejectLaunch";
import FormRejectReason from "./FormRejectReason";

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("draft status", () => {
    return <Subject />;
  })
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
