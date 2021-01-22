/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { storiesOf } from "@storybook/react";
import React from "react";
import { Subject } from "./mocks";

storiesOf("pages/EditAudience/FormAudience", module)
  .add("basic", () => <Subject onSubmit={action("submit")} />)
  .add("loading", () => <Subject isLoading />)
  .add("server/submit errors", () => (
    <Subject
      submitErrors={{
        "*": ["Big bad server thing happened"],
        channel: ["Cannot tune in this channel"],
        firefox_min_version: ["Bad min version"],
        targeting_config_slug: ["This slug is icky"],
        population_percent: ["This is not a percentage"],
        total_enrolled_clients: ["Need a number here, bud."],
        proposed_enrollment: ["Emoji are not numbers"],
        proposed_duration: ["No negative numbers"],
      }}
    />
  ));
