/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Button } from "react-bootstrap";
import { getStatus } from "src/lib/experiment";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

const RequestLiveUpdate = ({
  isLoading,
  onSubmit,
  experiment,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  experiment: getExperiment_experimentBySlug;
}) => {
  const status = getStatus(experiment);
  const shouldDisable =
    !status.dirty || status.review || status.approved || status.waiting;

  return (
    <div className="mb-4" data-testid="update-live-to-review">
      <Button
        data-testid="request-update-button"
        id="request-update-button"
        type="button"
        className="mr-2 btn btn-primary"
        disabled={isLoading || shouldDisable}
        onClick={onSubmit}
      >
        Request Update
      </Button>
    </div>
  );
};

export default RequestLiveUpdate;
