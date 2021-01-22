/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import ExperimentNotFound from ".";

storiesOf("pages/ExperimentNotFound", module)
  .addDecorator(withLinks)
  .add("basic", () => <ExperimentNotFound slug="foo-bar-baz" />);
