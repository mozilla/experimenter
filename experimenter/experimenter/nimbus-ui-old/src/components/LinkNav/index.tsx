/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link, useLocation } from "@reach/router";
import classNames from "classnames";
import React from "react";
import { Button } from "react-bootstrap";
import Nav from "react-bootstrap/Nav";
import { BASE_PATH } from "src/lib/constants";

type LinkNavProps = {
  children: React.ReactNode;
  disabled?: boolean;
  route?: string;
  testid?: string;
  className?: string;
  textColor?: string;
  title?: string;
  onClick?: () => void;
  useButton?: boolean;
  relativeToRoot?: boolean;
};

export const LinkNav = ({
  route,
  children,
  disabled = false,
  testid = "nav-home",
  className = "mx-1 my-2",
  textColor,
  title,
  onClick,
  useButton = false,
  relativeToRoot = false,
}: LinkNavProps) => {
  const location = useLocation();
  const to = route
    ? relativeToRoot
      ? `${route}`
      : `${BASE_PATH}/${route}`
    : BASE_PATH;
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
      ) : useButton ? (
        <Button
          {...{ title }}
          variant="link"
          href={relativeToRoot ? to : ""}
          className={classNames(
            textColor,
            "d-flex font-weight-semibold m-0 p-0 b-0 align-items-center",
          )}
          data-testid={testid}
          onClick={onClick}
        >
          {children}
        </Button>
      ) : (
        <Link
          {...{ to, title }}
          className={classNames(textColor, "d-flex align-items-center")}
          data-testid={testid}
          onClick={onClick}
        >
          {children}
        </Link>
      )}
    </Nav.Item>
  );
};

export default LinkNav;
