/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import classNames from "classnames";
import React from "react";
import Nav from "react-bootstrap/Nav";
import { BASE_PATH } from "../../lib/constants";

type LinkNavProps = {
  children: React.ReactNode;
  disabled?: boolean;
  route?: string;
  storiesOf: string;
  testid?: string;
  className?: string;
  textColor?: string;
  title?: string;
};

export const LinkNav = ({
  route,
  children,
  disabled = false,
  storiesOf,
  testid = "nav-home",
  className = "mx-1 my-2",
  textColor,
  title,
}: LinkNavProps) => {
  const to = route ? `${BASE_PATH}/${route}` : BASE_PATH;
  // an alternative to reach-router's `isCurrent` with identical
  // functionality; explicitly setting it here allows us to test.
  // eslint-disable-next-line
  const isCurrentPage = location.pathname === to;

  // If we supplied a text color, use it. Otherwise use current page colors
  textColor = textColor || (isCurrentPage ? "text-primary" : "text-dark");
  // But if the link is disabled, override any existing color
  textColor = disabled ? "text-muted" : textColor;

  return (
    <Nav.Item as="li" {...{ className }}>
      {disabled ? (
        <span
          className={classNames(textColor, "d-flex align-items-center")}
          data-testid={testid}
          {...{ title }}
        >
          {children}
        </span>
      ) : (
        <Link
          {...{ to, title }}
          data-sb-kind={storiesOf}
          className={classNames(textColor, "d-flex align-items-center")}
          data-testid={testid}
        >
          {children}
        </Link>
      )}
    </Nav.Item>
  );
};
