/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { Subject } from "./mocks";

storiesOf("components/AppLayoutWithSidebar", module)
  .addDecorator(withLinks)
  .add("basic", () => <Subject />)
  .add("missing details", () => (
    <Subject
      review={{
        __typename: "NimbusReadyForReviewType",
        ready: false,
        message: {
          reference_branch: ["This field may not be null."],
          channel: ["This field may not be null."],
        },
      }}
    />
  ))
  .add("status: review", () => (
    <Subject status={NimbusExperimentStatus.REVIEW} />
  ))
  .add("status: accepted", () => (
    <Subject status={NimbusExperimentStatus.ACCEPTED} />
  ))
  .add("status: live", () => <Subject status={NimbusExperimentStatus.LIVE} />);
