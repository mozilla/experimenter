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
import { print } from "graphql";
import { GET_EXPERIMENT_QUERY } from "../gql/experiments";
import { getExperiment } from "../types/getExperiment";

export interface MockedProps {
  childProps?: object;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
}

export interface MockedState {
  client: ApolloClient<any>;
}

// Disabling this rule for now because we'll eventually
// be using props from MockedProps.
// eslint-disable-next-line no-empty-pattern
export function createCache({}: MockedProps = {}) {
  const cache = new InMemoryCache();

  // As we set up new cached queries we can use
  // `cache.writeQuery` to set up default data
  // in tests with values set in MockedProps
  //
  // cache.writeQuery({
  //   query: MY_QUERY,
  //   data: {
  //     queryDataDefault,
  //   },
  // });

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
    public addTypename: Boolean = true,
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
      let timer = setTimeout(
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
) => {
  // If `null` is explicitely passed in for `modifications`, the experiment
  // data will be `null`.
  const experiment =
    modifications === null
      ? null
      : Object.assign(
          {
            __typename: "NimbusExperimentType",
            name: "Open-architected background installation",
            slug,
            status: "DRAFT",
            hypothesis: "Realize material say pretty.",
            application: "FIREFOX_DESKTOP",
            publicDescription:
              "Official approach present industry strategy dream piece.",
            controlBranch: {
              __typename: "NimbusBranchType",
              name: "User-centric mobile solution",
              slug: "user-centric-mobile-solution",
              description:
                "Behind almost radio result personal none future current.",
              ratio: 1,
              featureValue: '{"environmental-fact": "really-citizen"}',
              featureEnabled: true,
            },
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
            probeSets: [
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
    data: experiment as getExperiment["experimentBySlug"],
  };
};
