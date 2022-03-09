/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Operation } from "@apollo/client";
import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageReporting from ".";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { MockedCache, SimulatedMockLink } from "../../lib/mocks";

storiesOf("pages/New", module)
  .addDecorator(withLinks)
  .add("basic", () => <Subject />);

const actionCreateExperiment = action("createExperiment");

const mkSimulatedQueries = ({
  message = "success" as string | Record<string, any>,
  status = 200,
  nimbusExperiment = { slug: "foo-bar-baz" },
} = {}) => [
  {
    request: {
      query: CREATE_EXPERIMENT_MUTATION,
    },
    delay: 1000,
    result: (operation: Operation) => {
      const { name, application, hypothesis, changelogMessage } =
        operation.variables.input;
      actionCreateExperiment(name, application, hypothesis, changelogMessage);
      return {
        data: {
          createExperiment: {
            message,
            status,
            nimbusExperiment,
          },
        },
      };
    },
  },
];

const Subject = ({ simulatedQueries = mkSimulatedQueries() }) => {
  const mockLink = new SimulatedMockLink(simulatedQueries, false);
  return (
    <MockedCache link={mockLink}>
      <PageReporting />
    </MockedCache>
  );
};
