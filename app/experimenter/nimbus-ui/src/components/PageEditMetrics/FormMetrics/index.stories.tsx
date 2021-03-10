/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { storiesOf } from "@storybook/react";
import React from "react";
import { mockExperimentQuery } from "../../../lib/mocks";
import { Subject } from "./mocks";

const onSave = action("onSave");
const onNext = action("onNext");

storiesOf("pages/EditMetrics/FormMetrics", module)
  .add("basic", () => <Subject {...{ onSave, onNext }} />)
  .add("loading", () => <Subject isLoading {...{ onSave, onNext }} />)
  .add("server/submit errors", () => (
    <Subject
      submitErrors={{
        "*": ["Big bad server thing broke!"],
        primary_outcomes: ["Your primary outcomes stink."],
        secondary_outcomes: ["Your secondary outcomes stink."],
      }}
      {...{ onSave, onNext }}
    />
  ))
  .add("with experiment", () => {
    const { experiment } = mockExperimentQuery("boo");
    return <Subject {...{ experiment, onSave, onNext }} />;
  });
