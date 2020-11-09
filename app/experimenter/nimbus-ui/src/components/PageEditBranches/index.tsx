/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import { useConfig } from "../../hooks";
import FormBranches from "../FormBranches";
import LinkExternal from "../LinkExternal";
import AppLayoutWithSidebarAndData from "../AppLayoutWithSidebarAndData";

// TODO: find this doco URL
const BRANCHES_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FJT&title=Project+Nimbus";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { featureConfig } = useConfig();

  return (
    <AppLayoutWithSidebarAndData title="Branches" testId="PageEditBranches">
      {({ experiment }) => (
        <>
          <p>
            If you want, you can add a <strong>feature flag</strong>{" "}
            configuration to each branch. Experiments can only change one flag
            at a time.{" "}
            <LinkExternal href={BRANCHES_DOC_URL}>Learn more</LinkExternal>
          </p>
          {/* TODO: EXP-505 for accepting and saving edits to branches */}
          <FormBranches
            {...{
              experiment,
              featureConfig,
              // TODO: supply this as default value, track changes within FormBranches
              equalRatio: false,
            }}
          />
        </>
      )}
    </AppLayoutWithSidebarAndData>
  );
};

export default PageEditBranches;
