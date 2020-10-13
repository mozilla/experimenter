/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import LinkExternal from "./index";
import { ReactComponent as OpenExternalIcon } from "./open-external.svg";

storiesOf("Components/LinkExternal", module).add("basic", () => (
  <p className="m-3">
    <LinkExternal href="https://mozilla.org">
      Keep the internet open and accessible to all.
      <OpenExternalIcon
        className="inline-block w-3 h-3 ml-1"
        aria-hidden="true"
      />
    </LinkExternal>
  </p>
));
