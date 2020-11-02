/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import PageEditContainer from "../PageEditContainer";

type PageRequestReviewProps = {} & RouteComponentProps;

const PageRequestReview: React.FunctionComponent<PageRequestReviewProps> = () => (
  <PageEditContainer title="Review & Launch" testId="PageRequestReview">
    {({ experiment }) => <p>{experiment.name}</p>}
  </PageEditContainer>
);

export default PageRequestReview;
