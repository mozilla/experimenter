/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams, Link } from "@reach/router";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";
import { BASE_PATH } from "../../lib/constants";
import classNames from "classnames";
import { ReactComponent as ChevronLeft } from "./chevron-left.svg";
import { ReactComponent as Cog } from "./cog.svg";
import { ReactComponent as Layers } from "./layers.svg";
import { ReactComponent as ChartArrow } from "./chart-arrow.svg";
import { ReactComponent as Person } from "./person.svg";
import { ReactComponent as Clipboard } from "./clipboard.svg";
import { ReactComponent as NotAllowed } from "./not-allowed.svg";
import { ReactComponent as AlertCircle } from "./alert-circle.svg";

type AppLayoutWithSidebarProps = {
  testid?: string;
  children: React.ReactNode;
  // TODO: Will be updated as part of EXP-464 and EXP-466
  review?: {
    invalidPages: string[];
    ready: boolean;
  };
} & RouteComponentProps;

const editPages = [
  {
    name: "Overview",
    slug: "overview",
    icon: <Cog className="mr-3" width="18" height="18" />,
  },
  {
    name: "Branches",
    slug: "branches",
    icon: <Layers className="mr-3" width="18" height="18" />,
  },
  {
    name: "Metrics",
    slug: "metrics",
    icon: <ChartArrow className="mr-3" width="18" height="18" />,
  },
  {
    name: "Audience",
    slug: "audience",
    icon: <Person className="mr-3" width="18" height="18" />,
  },
];

export const AppLayoutWithSidebar = ({
  children,
  testid = "AppLayoutWithSidebar",
  review,
}: AppLayoutWithSidebarProps) => {
  const { slug } = useParams();

  return (
    <Container fluid className="h-100vh" data-testid={testid}>
      <Row className="h-md-100">
        <Col
          md="3"
          lg="3"
          xl="2"
          className="bg-light pt-2 border-right shadow-sm"
        >
          <nav data-testid="nav-sidebar">
            <Nav className="flex-column font-weight-semibold" as="ul">
              <LinkNav
                storiesOf="pages/Home"
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Experiments
              </LinkNav>
              {editPages.map((page, idx) => (
                <LinkNav
                  key={`sidebar-${page.name}-${idx}`}
                  route={`${slug}/edit/${page.slug}`}
                  storiesOf={`pages/Edit${page.name}`}
                  testid={`nav-edit-${page.slug}`}
                >
                  {page.icon}
                  {page.name}
                  {review?.invalidPages.includes(page.slug) && (
                    <AlertCircle
                      className="ml-3"
                      width="18"
                      height="18"
                      data-testid={`missing-detail-alert-${page.slug}`}
                    />
                  )}
                </LinkNav>
              ))}
              {!review || review.ready ? (
                <LinkNav
                  route={`${slug}/request-review`}
                  storiesOf="pages/RequestReview"
                  testid="nav-request-review"
                >
                  <Clipboard className="mr-3" width="18" height="18" />
                  Review &amp; Launch
                </LinkNav>
              ) : (
                <MissingDetails
                  experimentSlug={slug}
                  invalidPages={review.invalidPages}
                />
              )}
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main className="container-lg mx-auto">{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

type LinkNavProps = {
  children: React.ReactNode;
  route?: string;
  storiesOf: string;
  testid?: string;
  className?: string;
  textColor?: string;
};

const LinkNav = ({
  route,
  children,
  storiesOf,
  testid = "nav-home",
  className,
  textColor,
}: LinkNavProps) => {
  const to = route ? `${BASE_PATH}/${route}` : BASE_PATH;
  // an alternative to reach-router's `isCurrent` with identical
  // functionality; explicitely setting it here allows us to test.
  // eslint-disable-next-line
  const isCurrentPage = location.pathname === to;
  return (
    <Nav.Item as="li" className={classNames("mx-1 my-2", className)}>
      <Link
        {...{ to }}
        data-sb-kind={storiesOf}
        className={classNames(
          textColor ? textColor : isCurrentPage ? "text-primary" : "text-dark",
          "d-flex align-items-center",
        )}
        data-testid={testid}
      >
        {children}
      </Link>
    </Nav.Item>
  );
};

type MissingDetailsProps = {
  experimentSlug: string;
  invalidPages: string[];
};

const MissingDetails = ({
  experimentSlug,
  invalidPages,
}: MissingDetailsProps) => (
  <div
    className="mx-1 my-2 d-flex text-muted font-weight-normal"
    data-testid="missing-details"
  >
    <NotAllowed className="mr-3 mt-1" width="18" height="18" />
    <div>
      <p className="mb-1">Review &amp; Launch</p>
      <p className="mt-0 small">
        Missing details in:{" "}
        {invalidPages.map((missingPage, idx) => {
          const editPage = editPages.find((p) => p.slug === missingPage)!;

          return (
            <React.Fragment key={`missing-${idx}`}>
              <Link
                data-sb-kind={`pages/Edit${editPage.name}`}
                data-testid={`missing-detail-link-${editPage.slug}`}
                to={`${BASE_PATH}/${experimentSlug}/edit/${editPage.slug}`}
              >
                {editPage.name}
              </Link>

              {idx !== invalidPages.length - 1 && ", "}
            </React.Fragment>
          );
        })}
      </p>
    </div>
  </div>
);

export default AppLayoutWithSidebar;
