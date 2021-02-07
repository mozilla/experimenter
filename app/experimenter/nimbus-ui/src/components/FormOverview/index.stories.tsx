/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { storiesOf } from "@storybook/react";
import React from "react";
import { MockExperimentContextProvider } from "../../lib/mocks";
import { Subject } from "./mocks";

const onSubmit = action("onSubmit");
const onCancel = action("onCancel");
const onNext = action("onNext");

storiesOf("components/FormOverview", module)
  .add("basic", () => <Subject {...{ onSubmit, onCancel }} />)
  .add("loading", () => <Subject isLoading {...{ onSubmit, onCancel }} />)
  .add("server/submit errors", () => (
    <Subject
      submitErrors={{
        "*": ["Big bad server thing broke!"],
        name: ["This name is terrible."],
        hypothesis: ["You call this a hypothesis?"],
        application: ["That's a potato."],
      }}
      {...{ onSubmit, onCancel }}
    />
  ))
  .add("with experiment", () => {
    return (
      <MockExperimentContextProvider>
        <Subject {...{ onSubmit, onNext }} />
      </MockExperimentContextProvider>
    );
  });
