/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";

const NotSet = ({
  copy = "Not set",
  "data-testid": testid = "not-set",
  color = "text-danger",
}: {
  copy?: string;
  "data-testid"?: string;
  color?: string;
}) => (
  <span className={color} data-testid={testid}>
    {copy}
  </span>
);

export default NotSet;
