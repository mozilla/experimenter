/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import { Subject } from "./mocks";

const onSubmit = action("onSubmit");

storiesOf("pages/RequestReview/FormRequestReview", module)
  .addDecorator(withLinks)
  .add("success", () => <Subject {...{ onSubmit }} />)
  .add("error", () => <Subject {...{ onSubmit, submitError: "Uh oh!" }} />);
