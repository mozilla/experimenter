/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";

type AppLayoutProps = {
  children: React.ReactNode;
};

// TODO: Depending on the main page ("directory view") design, we may want two
// AppLayouts - one with a header/footer, and another with a nav sidebar.

export const AppLayout = ({ children }: AppLayoutProps) => {
  return <main data-testid="main">{children}</main>;
};

export default AppLayout;
