import React from "react";
import { AppErrorAlert } from ".";

export default {
  title: "components/AppErrorAlert",
  component: AppErrorAlert,
};

export const withoutErrorMessage = () => <AppErrorAlert error={new Error()} />;

export const withErrorMessage = () => (
  <AppErrorAlert error={new Error("Uh oh. You made the app crashy crash.")} />
);
