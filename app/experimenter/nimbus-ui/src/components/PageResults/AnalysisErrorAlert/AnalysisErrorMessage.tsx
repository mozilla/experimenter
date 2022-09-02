/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { AnalysisError } from "../../../lib/visualization/types";

type AnalysisErrorMessageProps = {
  err: AnalysisError;
};

const AnalysisErrorMessage = ({ err }: AnalysisErrorMessageProps) => {
  let alertMessage = '';
  if (err.exception_type) {
    alertMessage += err.exception_type;
  } else {
    alertMessage += "Unknown error";
  }
  if (err.statistic) {
    alertMessage += ` calculating ${err.statistic}`;
  }
  return (
    <>
      <hr />
      <p><b>{alertMessage}</b>: {err.message}</p>
    </>
  );
};

export default React.memo(AnalysisErrorMessage);