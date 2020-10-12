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
