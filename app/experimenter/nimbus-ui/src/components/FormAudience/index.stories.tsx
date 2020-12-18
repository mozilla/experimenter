/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import { Subject } from "./mocks";

storiesOf("components/FormAudience", module)
  .add("basic", () => <Subject onSubmit={action("submit")} />)
  .add("loading", () => <Subject isLoading />)
  .add("server/submit errors", () => (
    <Subject
      submitErrors={{
        "*": ["Big bad server thing happened"],
        channel: ["Cannot tune in this channel"],
        firefoxMinVersion: ["Bad min version"],
        targetingConfigSlug: ["This slug is icky"],
        populationPercent: ["This is not a percentage"],
        totalEnrolledClients: ["Need a number here, bud."],
        proposedEnrollment: ["Emoji are not numbers"],
        proposedDuration: ["No negative numbers"],
      }}
    />
  ));
