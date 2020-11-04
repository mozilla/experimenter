/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  InMemoryCache,
  ApolloClient,
  ApolloProvider,
  ApolloLink,
  Operation,
  FetchResult,
} from "@apollo/client";
import { Observable } from "@apollo/client/utilities";
import { MockLink, MockedResponse } from "@apollo/client/testing";
import { equal } from "@wry/equality";
import { DocumentNode, print } from "graphql";
import { GET_EXPERIMENT_QUERY } from "../gql/experiments";
import { getExperiment } from "../types/getExperiment";
import { getConfig_nimbusConfig } from "../types/getConfig";
import { GET_CONFIG_QUERY } from "../gql/config";
import {
  NimbusFeatureConfigApplication,
  NimbusProbeKind,
} from "../types/globalTypes";

export interface MockedProps {
  config?: Partial<typeof MOCK_CONFIG> | null;
  childProps?: object;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
}

export interface MockedState {
  client: ApolloClient<any>;
}

export const MOCK_CONFIG: getConfig_nimbusConfig = {
  __typename: "NimbusConfigurationType",
  application: [
    {
      __typename: "NimbusLabelValueType",
      label: "Desktop",
      value: "DESKTOP",
    },
  ],
  channels: [
    {
      __typename: "NimbusLabelValueType",
      label: "Desktop Beta",
      value: "DESKTOP_BETA",
    },
  ],
  featureConfig: [
    {
      __typename: "NimbusFeatureConfigType",
      id: "1",
      name: "Up-sized cohesive complexity",
      slug: "up-sized-cohesive-complexity",
      description:
        "Quickly above also mission action. Become thing item institution plan.\nImpact friend wonder. Interview strategy nature question. Admit room without impact its enter forward.",
      application: NimbusFeatureConfigApplication.FENIX,
      ownerEmail: "sheila43@yahoo.com",
      schema: null,
    },
    {
      __typename: "NimbusFeatureConfigType",
      id: "2",
      name: "Mauris odio erat",
      slug: "mauris-odio-erat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusFeatureConfigApplication.FENIX,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
  ],
  firefoxMinVersion: [
    {
      __typename: "NimbusLabelValueType",
      label: "Firefox 80",
      value: "FIREFOX_80",
    },
  ],
  probeSets: [
    {
      __typename: "NimbusProbeSetType",
      id: "1",
      name: "Inverse responsive methodology",
      slug: "inverse-responsive-methodology",
      probes: [
        {
          __typename: "NimbusProbeType",
          id: "1",
          kind: NimbusProbeKind.EVENT,
          name: "Public-key intangible Graphical User Interface",
          eventCategory: "persevering-intangible-productivity",
          eventMethod: "monitored-system-worthy-core",
          eventObject: "ameliorated-uniform-protocol",
          eventValue: "front-line-5thgeneration-product",
        },
        {
          __typename: "NimbusProbeType",
          id: "2",
          kind: NimbusProbeKind.SCALAR,
          name: "Total didactic moderator",
          eventCategory: "horizontal-bifurcated-attitude",
          eventMethod: "optimized-homogeneous-system-engine",
          eventObject: "virtual-discrete-customer-loyalty",
          eventValue: "automated-national-infrastructure",
        },
      ],
    },
  ],
  targetingConfigSlug: [
    {
      __typename: "NimbusLabelValueType",
      label: "First Run",
      value: "FIRST_RUN",
    },
  ],
};

// Disabling this rule for now because we'll eventually
// be using props from MockedProps.
// eslint-disable-next-line no-empty-pattern
export function createCache({ config = {} }: MockedProps = {}) {
  const cache = new InMemoryCache();

  cache.writeQuery({
    query: GET_CONFIG_QUERY,
    data: {
      nimbusConfig: { ...MOCK_CONFIG, ...config },
    },
  });

  return cache;
}

export class MockedCache extends React.Component<MockedProps, MockedState> {
  constructor(props: MockedProps) {
    super(props);
    this.state = {
      client: new ApolloClient({
        cache: createCache(props),
        link: new MockLink(props.mocks || [], true),
      }),
    };
  }

  render() {
    const { children, childProps } = this.props;
    return children ? (
      <ApolloProvider client={this.state.client}>
        {React.cloneElement(React.Children.only(children), { ...childProps })}
      </ApolloProvider>
    ) : null;
  }

  componentWillUnmount() {
    this.state.client.stop();
  }
}

type ResultFunction = (operation: Operation) => FetchResult;

type SimulatedMockedResponses = ReadonlyArray<{
  request: MockedResponse["request"];
  result: ResultFunction;
  delay?: number;
}>;

export class SimulatedMockLink extends ApolloLink {
  constructor(
    public mockedResponses: SimulatedMockedResponses,
    public addTypename: boolean = true,
  ) {
    super();
  }

  public request(operation: Operation): Observable<FetchResult> | null {
    const response = this.mockedResponses.find((response) =>
      equal(operation.query, response.request.query),
    );

    if (!response) {
      this.onError(
        new Error(
          `No more mocked responses for the query: ${print(
            operation.query,
          )}, variables: ${JSON.stringify(operation.variables)}`,
        ),
      );
      return null;
    }

    const { result, delay } = response!;

    return new Observable((observer) => {
      const timer = setTimeout(
        () => {
          observer.next(
            typeof result === "function"
              ? (result(operation) as FetchResult)
              : result,
          );
          observer.complete();
        },
        delay ? delay : 0,
      );

      return () => clearTimeout(timer);
    });
  }
}

export const mockExperimentQuery = (
  slug: string,
  modifications: Partial<getExperiment["experimentBySlug"]> = {},
): {
  mock: MockedResponse<Record<string, any>>;
  data: getExperiment["experimentBySlug"];
} => {
  // If `null` is explicitely passed in for `modifications`, the experiment
  // data will be `null`.
  const experiment: getExperiment["experimentBySlug"] =
    modifications === null
      ? null
      : Object.assign(
          {
            __typename: "NimbusExperimentType",
            id: "1",
            name: "Open-architected background installation",
            slug,
            status: "DRAFT",
            hypothesis: "Realize material say pretty.",
            application: "DESKTOP",
            publicDescription:
              "Official approach present industry strategy dream piece.",
            referenceBranch: {
              __typename: "NimbusBranchType",
              name: "User-centric mobile solution",
              slug: "user-centric-mobile-solution",
              description:
                "Behind almost radio result personal none future current.",
              ratio: 1,
              featureValue: '{"environmental-fact": "really-citizen"}',
              featureEnabled: true,
            },
            featureConfig: null,
            treatmentBranches: [
              {
                __typename: "NimbusBranchType",
                name: "Managed zero tolerance projection",
                slug: "managed-zero-tolerance-projection",
                description: "Next ask then he in degree order.",
                ratio: 1,
                featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
                featureEnabled: true,
              },
            ],
            primaryProbeSets: [
              {
                __typename: "NimbusProbeSetType",
                slug: "enterprise-wide-exuding-focus-group",
                name: "Enterprise-wide exuding focus group",
              },
            ],
            secondaryProbeSets: [
              {
                __typename: "NimbusProbeSetType",
                slug: "enterprise-wide-exuding-focus-group",
                name: "Enterprise-wide exuding focus group",
              },
            ],
            channels: ["Nightly", "Beta"],
            firefoxMinVersion: "A_83_",
            targetingConfigSlug: "US_ONLY",
            populationPercent: 40,
            totalEnrolledClients: 68000,
            proposedEnrollment: 15,
          },
          modifications,
        );

  return {
    mock: {
      request: {
        query: GET_EXPERIMENT_QUERY,
        variables: {
          slug,
        },
      },
      result: {
        data: {
          experimentBySlug: experiment,
        },
      },
    },
    data: experiment,
  };
};

export const mockExperimentMutation = (
  mutation: DocumentNode,
  input: Record<string, string>,
  key: string,
  {
    status = 200,
    message = "success",
    experiment,
  }: {
    status?: number;
    message?: string | Record<string, any>;
    experiment?: Record<string, any> | null;
  },
) => {
  return {
    request: {
      query: mutation,
      variables: {
        input,
      },
    },
    result: {
      errors: undefined as undefined | any[],
      data: {
        [key]: {
          clientMutationId: "8675309",
          message,
          status,
          nimbusExperiment: experiment,
        },
      },
    },
  };
};
