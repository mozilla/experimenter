/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  FetchResult,
  InMemoryCache,
  Operation,
} from "@apollo/client";
import { MockedResponse, MockLink } from "@apollo/client/testing";
import { Observable } from "@apollo/client/utilities";
import { equal } from "@wry/equality";
import { DocumentNode, print } from "graphql";
import React from "react";
import { GET_CONFIG_QUERY } from "../gql/config";
import {
  GET_EXPERIMENTS_QUERY,
  GET_EXPERIMENT_QUERY,
} from "../gql/experiments";
import { ExperimentReview } from "../hooks";
import { cacheConfig } from "../services/apollo";
import {
  getAllExperiments,
  getAllExperiments_experiments,
} from "../types/getAllExperiments";
import { getConfig_nimbusConfig } from "../types/getConfig";
import {
  getExperiment,
  getExperiment_experimentBySlug,
} from "../types/getExperiment";
import {
  ExperimentInput,
  NimbusDocumentationLinkTitle,
  NimbusExperimentStatus,
  NimbusFeatureConfigApplication,
} from "../types/globalTypes";
import { getStatus } from "./experiment";

export interface MockedProps {
  config?: Partial<typeof MOCK_CONFIG> | null;
  childProps?: object;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
  addTypename?: boolean;
  link?: ApolloLink;
}

export interface MockedState {
  client: ApolloClient<any>;
}

export const MOCK_CONFIG: getConfig_nimbusConfig = {
  application: [
    {
      label: "Desktop",
      value: "DESKTOP",
    },
  ],
  channel: [
    {
      label: "Desktop Beta",
      value: "BETA",
    },
    {
      label: "Desktop Nightly",
      value: "NIGHTLY",
    },
    {
      label: "Platypus Doorstop",
      value: "PLATYPUS_DOORSTOP",
    },
  ],
  featureConfig: [
    {
      id: "1",
      name: "Picture-in-Picture",
      slug: "picture-in-picture",
      description:
        "Quickly above also mission action. Become thing item institution plan.\nImpact friend wonder. Interview strategy nature question. Admit room without impact its enter forward.",
      application: NimbusFeatureConfigApplication.FENIX,
      ownerEmail: "sheila43@yahoo.com",
      schema: null,
    },
    {
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
      label: "Firefox 80",
      value: "FIREFOX_83",
    },
  ],
  probeSets: [
    {
      name: "Probe Set A",
      slug: "probe-set-a",
    },
    {
      name: "Probe Set B",
      slug: "probe-set-b",
    },
    {
      name: "Probe Set C",
      slug: "probe-set-c",
    },
  ],
  targetingConfigSlug: [
    {
      label: "Us Only",
      value: "US_ONLY",
    },
  ],
  hypothesisDefault: "Enter a hypothesis",
  documentationLink: [
    {
      value: "DS_JIRA",
      label: "Data Science Jira Ticket",
    },
    {
      value: "DESIGN_DOC",
      label: "Experiment Design Document",
    },
    {
      value: "ENG_TICKET",
      label: "Engineering Ticket (Bugzilla/Jira/Github)",
    },
  ],
};

// Disabling this rule for now because we'll eventually
// be using props from MockedProps.
// eslint-disable-next-line no-empty-pattern
export function createCache({ config = {} }: MockedProps = {}) {
  const cache = new InMemoryCache(cacheConfig);

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
        link:
          props.link ||
          new MockLink(props.mocks || [], props.addTypename || true),
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

export function mockExperiment<
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug
>(modifications: Partial<getExperiment["experimentBySlug"]> = {}): T {
  return Object.assign(
    {
      id: 1,
      owner: {
        email: "example@mozilla.com",
      },
      name: "Open-architected background installation",
      slug: "open-architected-background-installation",
      status: "DRAFT",
      isEndRequested: false,
      monitoringDashboardUrl: "https://grafana.telemetry.mozilla.org",
      hypothesis: "Realize material say pretty.",
      application: "DESKTOP",
      publicDescription:
        "Official approach present industry strategy dream piece.",
      referenceBranch: {
        name: "User-centric mobile solution",
        slug: "user-centric-mobile-solution",
        description: "Behind almost radio result personal none future current.",
        ratio: 1,
        featureValue: '{"environmental-fact": "really-citizen"}',
        featureEnabled: true,
      },
      featureConfig: null,
      treatmentBranches: [
        {
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
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
      ],
      secondaryProbeSets: [
        {
          slug: "feature_b",
          name: "Feature B",
        },
      ],
      channel: "NIGHTLY",
      firefoxMinVersion: "FIREFOX_83",
      targetingConfigSlug: "US_ONLY",
      jexlTargetingExpression: "localeLanguageCode == 'en' && region == 'US'",
      populationPercent: "40",
      totalEnrolledClients: 68000,
      proposedEnrollment: 1,
      proposedDuration: 28,
      readyForReview: {
        ready: true,
        message: {},
      },
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 12096e5).toISOString(),
      riskMitigationLink: "https://docs.google.com/document/d/banzinga/edit",
      documentationLinks: [
        {
          title: NimbusDocumentationLinkTitle.DS_JIRA,
          link: "https://bingo.bongo",
        },
      ],
      isEnrollmentPaused: true,
      enrollmentEndDate: null,
    },
    modifications,
  ) as T;
}

export function mockExperimentQuery<
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug
>(
  slug = "foo",
  modifications: Partial<getExperiment["experimentBySlug"]> = {},
): {
  mock: MockedResponse<Record<string, any>>;
  experiment: T;
} {
  const experiment =
    modifications === null ? null : mockExperiment({ slug, ...modifications });

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
    experiment: experiment as T,
  };
}

export const MOCK_REVIEW: ExperimentReview = {
  ready: true,
  invalidPages: [],
  missingFields: [],
  isMissingField: () => false,
  refetch: () => {},
};

export const mockExperimentMutation = (
  mutation: DocumentNode,
  input: ExperimentInput,
  key: string,
  {
    status,
    message,
    experiment,
  }: {
    status?: number;
    message?: string | Record<string, any>;
    experiment?: Record<string, any> | null;
  } = {
    status: 200,
    message: "success",
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
          message,
          status,
          nimbusExperiment: experiment,
        },
      },
    },
  };
};

export const mockGetStatus = (status: NimbusExperimentStatus | null) => {
  const { experiment } = mockExperimentQuery("boo", { status });
  return getStatus(experiment);
};

const fiveDaysAgo = new Date();
fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);

/** Creates a single mock experiment suitable for getAllExperiments queries.  */
export function mockSingleDirectoryExperiment(
  overrides: Partial<getAllExperiments_experiments> = {},
): getAllExperiments_experiments {
  return {
    slug: `some-experiment-${Math.round(Math.random() * 100)}`,
    owner: {
      username: "example@mozilla.com",
    },
    monitoringDashboardUrl:
      "https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=bug-1668861-pref-measure-set-to-default-adoption-impact-of-chang-release-81-83",
    name: "Open-architected background installation",
    status: NimbusExperimentStatus.COMPLETE,
    featureConfig: {
      slug: "newtab",
      name: "New tab",
    },
    proposedEnrollment: 7,
    proposedDuration: 28,
    startDate: fiveDaysAgo.toISOString(),
    endDate: new Date(Date.now() + 12096e5).toISOString(),
    isEndRequested: false,
    ...overrides,
  };
}

export function mockDirectoryExperiments(
  overrides: Partial<getAllExperiments_experiments>[] = [
    {
      status: NimbusExperimentStatus.DRAFT,
      startDate: null,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.PREVIEW,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.REVIEW,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.REVIEW,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      endDate: null,
    },
    {
      status: NimbusExperimentStatus.COMPLETE,
    },
    {
      featureConfig: null,
    },
  ],
): getAllExperiments_experiments[] {
  return overrides.map(mockSingleDirectoryExperiment);
}

/** Creates a bunch of experiments for the Directory page  */
export function mockDirectoryExperimentsQuery(
  overrides?: Partial<getAllExperiments_experiments>[],
): MockedResponse<getAllExperiments> {
  const experiments = mockDirectoryExperiments(overrides);
  return {
    request: {
      query: GET_EXPERIMENTS_QUERY,
    },
    result: {
      data: experiments.length ? { experiments } : null,
    },
  };
}
