/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { Button } from "react-bootstrap";

type DisabledButtonProps = {
  id: string;
  testId: string;
  disabled?: boolean;
  onClick?: () => void;
  children?: ReactNode;
};

export const DisabledButton = ({
  id,
  testId,
  disabled,
  onClick,
  children,
}: DisabledButtonProps) => (
  <Button
    id={id}
    data-testid={testId}
    disabled={disabled}
    onClick={onClick}
    className="mr-2 btn"
    style={{
      backgroundColor: { disabled } ? "btn-primary" : "btn-secondary",
    }}
  >
    {children}
  </Button>
);

export default DisabledButton;
