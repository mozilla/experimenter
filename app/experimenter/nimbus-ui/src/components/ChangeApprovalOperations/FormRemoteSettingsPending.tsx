/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import LinkExternal from "../LinkExternal";

const FormRemoteSettingsPending = ({
  isLoading,
  reviewUrl,
  actionDescription,
}: {
  isLoading: boolean;
  reviewUrl: string;
  actionDescription: string;
}) => {
  return (
    <Alert variant="secondary">
      <Form className="text-body">
        <p>
          <strong>Action required —</strong> Please review this change in Remote
          Settings to {actionDescription} this experiment
        </p>

        <div className="d-flex bd-highlight">
          <div>
            <LinkExternal
              data-testid="open-remote-settings"
              className={`mr-2 btn btn-primary${isLoading ? " disabled" : ""}`}
              href={reviewUrl}
            >
              Open Remote Settings
            </LinkExternal>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormRemoteSettingsPending;
