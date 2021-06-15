/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PreviewURL from ".";
import { getStatus } from "../../lib/experiment";
import { mockExperiment } from "../../lib/mocks";

export default {
  title: "components/PreviewURL",
  component: PreviewURL,
};

export const Basic = () => {
  const experiment = mockExperiment();
  const status = getStatus(experiment);

  return (
    <div className="p-3">
      <PreviewURL {...{ ...experiment, status }} />
    </div>
  );
};
