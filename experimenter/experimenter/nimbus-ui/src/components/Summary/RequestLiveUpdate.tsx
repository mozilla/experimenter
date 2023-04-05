/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Button } from "react-bootstrap";

const RequestLiveUpdate = ({
  isLoading,
  onSubmit,
}: {
  isLoading: boolean;
  onSubmit: () => void;
}) => {
  return (
    <div className="mb-4" data-testid="update-live-to-review">
      <Button
        data-testid="request-update-button"
        id="request-update-button"
        type="button"
        className="mr-2 btn btn-primary"
        disabled={isLoading}
        onClick={onSubmit}
      >
        Request Update
      </Button>
    </div>
  );
};

export default RequestLiveUpdate;
