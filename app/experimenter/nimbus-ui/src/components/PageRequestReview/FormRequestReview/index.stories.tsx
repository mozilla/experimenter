/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { Subject } from "./mocks";
import { action } from "@storybook/addon-actions";

const onSubmit = action("onSubmit");

storiesOf("pages/RequestReview/FormRequestReview", module)
  .addDecorator(withLinks)
  .add("success", () => <Subject {...{ onSubmit }} />)
  .add("error", () => <Subject {...{ onSubmit, submitError: "Uh oh!" }} />);
