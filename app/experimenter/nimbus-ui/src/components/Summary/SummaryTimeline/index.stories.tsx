/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import MockDate from "mockdate";
import React from "react";
import { NimbusExperimentStatusEnum } from "../../../types/globalTypes";
import { Subject } from "./mocks";

storiesOf("components/Summary/SummaryTimeline", module)
  .addDecorator((getStory) => (
    <div className="container-lg py-5">{getStory()}</div>
  ))
  .add("draft, review, accepted", () => <Subject />)
  .add("live", () => {
    MockDate.set("2020-12-06T14:52:44.704811+00:00");
    return <Subject status={NimbusExperimentStatusEnum.LIVE} />;
  })
  .add("complete", () => (
    <Subject status={NimbusExperimentStatusEnum.COMPLETE} />
  ))
  .add("missing details", () => (
    <Subject computedDurationDays={0} computedEnrollmentDays={0} />
  ));
