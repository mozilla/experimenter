import React from "react";
import { storiesOf } from "@storybook/react";
import { AppErrorAlert } from ".";

storiesOf("components/AppErrorAlert", module).add("basic", () => (
  <AppErrorAlert />
));
