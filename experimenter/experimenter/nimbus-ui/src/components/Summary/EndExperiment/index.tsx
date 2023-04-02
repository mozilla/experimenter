/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Button } from "react-bootstrap";

const EndExperiment = ({
  onSubmit,
  isLoading,
  isRollout,
}: {
  isLoading: boolean;
  isRollout: boolean;
  onSubmit: () => void;
}) => {
  return (
    <div className="mb-4" data-testid="experiment-end">
      {
        <Button
          variant="primary"
          onClick={onSubmit}
          data-testid="end-experiment-start"
          disabled={isLoading}
          className="px-3"
        >
          End {isRollout ? "Rollout" : "Experiment"}
        </Button>
      }
    </div>
  );
};

export default EndExperiment;
