/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import RichText from ".";

const text = `Who we are

Mozilla Manifesto: https://www.mozilla.org/about/manifesto
Mozilla Foundation: http://foundation.mozilla.org
Get Involved: www.mozilla.org/contribute
Leadership (should not link): mozilla.org/about/leadership/`;

storiesOf("components/RichText", module).add("basic", () => (
  <RichText {...{ text }} />
));
