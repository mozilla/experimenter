/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { Helmet } from "react-helmet";

const Head = ({ title, children }: { title: string; children?: ReactNode }) => (
  <Helmet>
    <title>{title} | Experimenter</title>
    {children}
  </Helmet>
);

export default Head;
