/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { ReactComponent as NotAllowed } from "./not-allowed.svg";

type DisabledItemProps = {
  name: string;
  testId: string;
  children: ReactNode;
};

export const DisabledItem = ({ name, children, testId }: DisabledItemProps) => (
  <div
    className="mx-1 my-2 d-flex text-muted font-weight-normal"
    data-testid={testId}
  >
    <NotAllowed className="mt-1 sidebar-icon" />
    <div>
      <p className="mb-1">{name}</p>
      <p className="mt-0 small">{children}</p>
    </div>
  </div>
);
