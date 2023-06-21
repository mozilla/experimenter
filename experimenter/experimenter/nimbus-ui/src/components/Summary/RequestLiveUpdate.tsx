/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import DisabledButton from "src/components/DisabledButton";

const RequestLiveUpdate = ({
  isLoading,
  onSubmit,
  disable,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  disable: boolean;
}) => {
  return (
    <div className="mb-4" data-testid="update-live-to-review">
      <DisabledButton
        id="request-update-button"
        testId="request-update-button"
        disabled={isLoading || disable}
        onClick={onSubmit}
      >
        Request Update
      </DisabledButton>
    </div>
  );
};

export default RequestLiveUpdate;
