import { storiesOf } from "@storybook/react";
import React from "react";
import { AppErrorAlert } from ".";

storiesOf("components/AppErrorAlert", module).add("basic", () => (
  <AppErrorAlert />
));
