/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Alert } from "react-bootstrap";
import { REFETCH_DELAY } from "../../hooks/useRefetchOnError";

export const RefetchAlert = ({ className = "mt-4" }) => (
  <Alert variant="warning" data-testid="refetch-alert" {...{ className }}>
    <Alert.Heading>Fetch Error</Alert.Heading>
    <p>
      An error occured.{" "}
      <b>This usually happens when Experimenter is mid-deploy.</b>
    </p>
    <p>
      Refetching will occur one time automatically in {REFETCH_DELAY / 1000}{" "}
      seconds.
    </p>
  </Alert>
);

export default RefetchAlert;
