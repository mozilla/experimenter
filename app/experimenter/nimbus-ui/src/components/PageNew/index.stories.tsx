/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Operation } from "@apollo/client";
import { MockedCache, SimulatedMockLink } from "../../lib/mocks";
import { storiesOf } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import { CREATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import PageNew from ".";
import { withLinks } from "@storybook/addon-links";

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
      const { name, application, hypothesis } = operation.variables.input;
      actionCreateExperiment(name, application, hypothesis);
      return {
        data: {
          createExperiment: {
            clientMutationId: "8675309",
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
    <MockedCache link={mockLink} addTypename={false}>
      <PageNew />
    </MockedCache>
  );
};
