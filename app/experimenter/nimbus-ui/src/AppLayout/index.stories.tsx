import React from "react";
import { storiesOf } from "@storybook/react";
import AppLayout from ".";

storiesOf("AppLayout", module).add("default", () => (
  <AppLayout>
    <p>App contents go here</p>
  </AppLayout>
));
