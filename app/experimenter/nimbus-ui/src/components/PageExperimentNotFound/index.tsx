/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import React from "react";
import { BASE_PATH } from "../../lib/constants";
import AppLayout from "../AppLayout";

const ExperimentNotFound = ({ slug }: { slug: string }) => (
  <AppLayout testid="not-found">
    <section className="text-center">
      <h1 className="h2">Experiment Not Found</h1>
      <p className="pt-3">
        The experiment with slug &quot;{slug}&quot; could not be found. ☹️
      </p>
      <Link
        to={BASE_PATH}
        data-sb-kind="pages/Home"
        data-testid="not-found-home"
      >
        Go Home
      </Link>
    </section>
  </AppLayout>
);

export default ExperimentNotFound;
