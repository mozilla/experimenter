/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { linkTo, withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageRequestReview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { createMutationMock, experiment, mock, SubjectEXP866 } from "./mocks";

storiesOf("pages/RequestReview", module)
  .addDecorator(withLinks)
  .add("success", () => (
    <RouterSlugProvider mocks={[mock, createMutationMock(experiment.id!)]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ))
  .add("error", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  ))
  .add("non-reviewable", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });

    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageRequestReview polling={false} />
      </RouterSlugProvider>
    );
  });

const commonEXP866Props = {
  onBackToDraft: linkTo("pages/RequestReview/EXP-866", "draft status"),
  onLaunchToPreview: linkTo("pages/RequestReview/EXP-866", "preview status"),
  onLaunchToReview: linkTo("pages/RequestReview/EXP-866", "review status"),
};

storiesOf("pages/RequestReview/EXP-866", module)
  .add("README", () => (
    <p className="mx-5 my-5">
      As part of <a href="https://jira.mozilla.com/browse/EXP-866">EXP-866</a>,{" "}
      these stories exercise an implementation of the UX flow designed for{" "}
      <a href="https://jira.mozilla.com/browse/EXP-628">EXP-628</a> (Launch to
      Preview)
    </p>
  ))
  .add("draft status", () => {
    return <SubjectEXP866 {...commonEXP866Props} />;
  })
  .add("preview status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      // @ts-ignore EXP-866 mock value until backend API & types are updated
      status: "PREVIEW",
    });
    return <SubjectEXP866 {...{ ...commonEXP866Props, mocks: [mock] }} />;
  })
  .add("review status", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    return <SubjectEXP866 {...{ ...commonEXP866Props, mocks: [mock] }} />;
  });
