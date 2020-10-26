/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayout from "../AppLayout";

const PageLoading = () => (
  <AppLayout testid="page-loading">
    <div className="text-center">
      <div
        className="spinner-border text-primary"
        role="status"
        data-testid="spinner"
      >
        <span className="sr-only">Loading...</span>
      </div>
    </div>
  </AppLayout>
);

export default PageLoading;
