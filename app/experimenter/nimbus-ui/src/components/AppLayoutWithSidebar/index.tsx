/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link, RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { ReactComponent as Clipboard } from "../../images/clipboard.svg";
import { ReactComponent as Cog } from "../../images/cog.svg";
import { BASE_PATH } from "../../lib/constants";
import { StatusCheck } from "../../lib/experiment";
import { DisabledItem } from "../DisabledItem";
import { LinkNav } from "../LinkNav";
import { ReactComponent as AlertCircle } from "./alert-circle.svg";
import { ReactComponent as ChartArrow } from "./chart-arrow.svg";
import { ReactComponent as Layers } from "./layers.svg";
import { ReactComponent as Person } from "./person.svg";

type AppLayoutWithSidebarProps = {
  testid?: string;
  children: React.ReactNode;
  status?: StatusCheck;
  review?: {
    invalidPages: string[];
    ready: boolean;
  };
} & RouteComponentProps;

const editPages = [
  {
    name: "Overview",
    slug: "overview",
    icon: <Cog className="sidebar-icon" />,
  },
  {
    name: "Branches",
    slug: "branches",
    icon: <Layers className="sidebar-icon" />,
  },
  {
    name: "Metrics",
    slug: "metrics",
    icon: <ChartArrow className="sidebar-icon" />,
  },
  {
    name: "Audience",
    slug: "audience",
    icon: <Person className="sidebar-icon" />,
  },
];

export const AppLayoutWithSidebar = ({
  children,
  testid = "AppLayoutWithSidebar",
  status,
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
          <nav data-testid="nav-sidebar" className="navbar">
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
                  disabled={status?.review}
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
              {!review || review.ready || status?.review ? (
                <LinkNav
                  route={`${slug}/request-review`}
                  storiesOf="pages/RequestReview"
                  testid="nav-request-review"
                >
                  <Clipboard className="sidebar-icon" />
                  Review &amp; Launch
                </LinkNav>
              ) : (
                <DisabledItem
                  name="Review &amp; Launch"
                  testId="missing-details"
                >
                  Missing details in:{" "}
                  {review.invalidPages.map((missingPage, idx) => {
                    const editPage = editPages.find(
                      (p) => p.slug === missingPage,
                    )!;

                    return (
                      <React.Fragment key={`missing-${idx}`}>
                        <Link
                          data-sb-kind={`pages/Edit${editPage.name}`}
                          data-testid={`missing-detail-link-${editPage.slug}`}
                          to={`${BASE_PATH}/${slug}/edit/${editPage.slug}?show-errors`}
                        >
                          {editPage.name}
                        </Link>

                        {idx !== review.invalidPages.length - 1 && ", "}
                      </React.Fragment>
                    );
                  })}
                </DisabledItem>
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

export default AppLayoutWithSidebar;
