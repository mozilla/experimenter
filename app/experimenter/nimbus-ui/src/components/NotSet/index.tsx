/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";

const NotSet = ({
  "data-testid": testid = "not-set",
}: {
  "data-testid"?: string;
}) => (
  <span className="text-danger" data-testid={testid}>
    Not set
  </span>
);

export default NotSet;
