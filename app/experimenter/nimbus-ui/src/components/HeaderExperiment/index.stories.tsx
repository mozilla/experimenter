/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { Subject } from "./mocks";

storiesOf("components/HeaderExperiment", module)
  .addDecorator(withLinks)
  .add("status: draft", () => <Subject />)
  .add("status: review", () => (
    <Subject experiment={{ status: NimbusExperimentStatus.REVIEW }} />
  ))
  .add("status: live", () => (
    <Subject experiment={{ status: NimbusExperimentStatus.LIVE }} />
  ))
  .add("status: complete", () => (
    <Subject experiment={{ status: NimbusExperimentStatus.COMPLETE }} />
  ))
  .add("includes dates", () => (
    <Subject experiment={{ status: NimbusExperimentStatus.REVIEW }} />
  ));
