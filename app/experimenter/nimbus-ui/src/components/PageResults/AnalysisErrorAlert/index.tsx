/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Alert } from "react-bootstrap";
import AnalysisErrorMessage from './AnalysisErrorMessage';
import { AnalysisError } from "../../../lib/visualization/types";

type AnalysisErrorAlertProps = {
  errors: AnalysisError[];
};

const AnalysisErrorAlert = ({ errors }: AnalysisErrorAlertProps) => (
  <Alert variant="danger">
    <Alert.Heading as="h5">Analysis errors during last run:</Alert.Heading>
    {errors.map((err, idx) => <AnalysisErrorMessage key={idx} err={err} />)}
    <hr />
    <p style={{ textAlign: 'right', marginBottom: 0 }}>
      <i>Contact{' '}
        <Alert.Link href="https://mozilla.slack.com/archives/CF94YGE03">#ask-experimenter</Alert.Link>
        {' '}with questions.</i></p>
  </Alert>
);

export default React.memo(AnalysisErrorAlert);
