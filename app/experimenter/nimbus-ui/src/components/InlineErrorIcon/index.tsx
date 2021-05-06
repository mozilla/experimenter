/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ReactTooltip from "react-tooltip";
import { ReactComponent as ErrorCircle } from "../../images/error-circle.svg";

const InlineErrorIcon = ({
  field,
  message,
}: {
  field: string;
  message: string;
}) => (
  <>
    <ErrorCircle
      width="20"
      height="20"
      className="ml-1"
      data-testid={`missing-${field}`}
      data-tip={message}
    />
    <ReactTooltip />
  </>
);

export default InlineErrorIcon;
