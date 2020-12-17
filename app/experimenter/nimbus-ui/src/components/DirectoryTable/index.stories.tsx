/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { mockDirectoryExperimentsFactory } from "../../lib/mocks";
import DirectoryTable, {
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
} from ".";

storiesOf("components/DirectoryTable", module)
  .addDecorator(withLinks)
  .add("basic", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory()}
      />
    );
  })
  .add("live", () => {
    return (
      <DirectoryLiveTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory()}
      />
    );
  })
  .add("complete", () => {
    return (
      <DirectoryCompleteTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory()}
      />
    );
  })
  .add("drafts", () => {
    return (
      <DirectoryDraftsTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory()}
      />
    );
  })
  .add("custom components", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory()}
        columns={[
          {
            label: "Testing column",
            component: ({ status }) => <td>Hello {status}</td>,
          },
        ]}
      />
    );
  })
  .add("missing owner", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory([{ owner: null }])}
      />
    );
  })
  .add("no feature", () => {
    return (
      <DirectoryTable
        title="Mocked Experiments"
        experiments={mockDirectoryExperimentsFactory([{ featureConfig: null }])}
      />
    );
  });
