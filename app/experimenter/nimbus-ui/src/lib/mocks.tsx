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
import { ReviewCheck } from "../hooks";
import { cacheConfig } from "../services/apollo";
import {
  getAllExperiments,
  getAllExperiments_experiments,
} from "../types/getAllExperiments";
import { getConfig_nimbusConfig } from "../types/getConfig";
import {
  getExperiment,
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_rejection_changedBy,
} from "../types/getExperiment";
import {
  ExperimentInput,
  NimbusDocumentationLinkTitle,
  NimbusExperimentApplication,
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../types/globalTypes";
import { getStatus } from "./experiment";
import { OutcomesList, OutcomeSlugs } from "./types";

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
    {
      label: "Toaster",
      value: "TOASTER",
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
      id: 1,
      name: "Picture-in-Picture",
      slug: "picture-in-picture",
      description:
        "Quickly above also mission action. Become thing item institution plan.\nImpact friend wonder. Interview strategy nature question. Admit room without impact its enter forward.",
      application: NimbusExperimentApplication.FENIX,
      ownerEmail: "sheila43@yahoo.com",
      schema: null,
    },
    {
      id: 2,
      name: "Mauris odio erat",
      slug: "mauris-odio-erat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusExperimentApplication.DESKTOP,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
    {
      id: 3,
      name: "Foo lila sat",
      slug: "foo-lila-sat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusExperimentApplication.IOS,
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
  outcomes: [
    {
      friendlyName: "Picture-in-Picture",
      slug: "picture_in_picture",
      application: NimbusExperimentApplication.DESKTOP,
      description: "foo",
    },
    {
      friendlyName: "Feature B",
      slug: "feature_b",
      application: NimbusExperimentApplication.DESKTOP,
      description: "bar",
    },
    {
      friendlyName: "Feature C",
      slug: "feature_c",
      application: NimbusExperimentApplication.DESKTOP,
      description: "baz",
    },
    {
      friendlyName: "Feature D",
      slug: "feature_d",
      application: NimbusExperimentApplication.FENIX,
      description: "blah",
    },
  ],
  targetingConfigSlug: [
    {
      label: "Us Only",
      value: "US_ONLY",
      applicationValues: ["DESKTOP"],
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
  maxPrimaryOutcomes: 2,
  kintoAdminUrl: "https://kinto.example.com/v1/admin/",
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
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug,
>(modifications: Partial<getExperiment["experimentBySlug"]> = {}): T {
  return Object.assign(
    {
      id: 1,
      owner: {
        email: "example@mozilla.com",
      },
      name: "Open-architected background installation",
      slug: "open-architected-background-installation",
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.IDLE,
      isEndRequested: false,
      monitoringDashboardUrl: "https://grafana.telemetry.mozilla.org",
      hypothesis: "Realize material say pretty.",
      application: "DESKTOP",
      publicDescription:
        "Official approach present industry strategy dream piece.",
      referenceBranch: {
        name: "User-centric mobile solution",
        slug: "control",
        description: "Behind almost radio result personal none future current.",
        ratio: 1,
        featureValue: '{"environmental-fact": "really-citizen"}',
        featureEnabled: true,
      },
      featureConfig: null,
      treatmentBranches: [
        {
          name: "Managed zero tolerance projection",
          slug: "treatment",
          description: "Next ask then he in degree order.",
          ratio: 1,
          featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
          featureEnabled: true,
        },
      ],
      primaryOutcomes: ["picture_in_picture"],
      secondaryOutcomes: ["feature_b"],
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
      computedEndDate: new Date(Date.now() + 12096e5).toISOString(),
      riskMitigationLink: "https://docs.google.com/document/d/banzinga/edit",
      documentationLinks: [
        {
          title: NimbusDocumentationLinkTitle.DS_JIRA,
          link: "https://bingo.bongo",
        },
      ],
      isEnrollmentPaused: true,
      enrollmentEndDate: null,
      recipeJson:
        '{"schemaVersion": "1.5.0", "slug": "pre-emptive-zero-tolerance-data-warehouse", "id": "pre-emptive-zero-tolerance-data-warehouse", "arguments": {}, "application": "", "appName": "firefox_ios", "appId": "", "channel": "", "userFacingName": "Pre-emptive zero tolerance data-warehouse", "userFacingDescription": "Analysis art mean sort serve stuff. Scene alone current television up write company. Without admit she occur total generation by mother. Environmental remember account huge drive policy play strong.", "isEnrollmentPaused": false, "bucketConfig": null, "probeSets": [], "outcomes": [{"slug": "example_config", "priority": "primary"}, {"slug": "newtab_visibility", "priority": "primary"}, {"slug": "picture_in_picture", "priority": "secondary"}], "branches": [{"slug": "horizontal-well-modulated-conglomeration", "ratio": 1, "feature": {"featureId": "decentralized-solution-oriented-neural-net", "enabled": true, "value": {"trouble-left-back": "west-receive"}}}, {"slug": "fully-configurable-context-sensitive-local-area-network", "ratio": 1, "feature": {"featureId": "decentralized-solution-oriented-neural-net", "enabled": true, "value": {"financial-school": "peace-light-might"}}}], "targeting": "localeLanguageCode == \'en\' && ((isFirstStartup && !(\'trailhead.firstrun.didSeeAboutWelcome\'|preferenceValue)) || experiment.slug in activeExperiments)", "startDate": null, "endDate": null, "proposedDuration": 60, "proposedEnrollment": 45, "referenceBranch": "horizontal-well-modulated-conglomeration", "featureIds": ["decentralized-solution-oriented-neural-net"]}',
      riskBrand: false,
      riskRevenue: true,
      riskPartnerRelated: false,
    },
    modifications,
  ) as T;
}

export function mockExperimentQuery<
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug,
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

export const MOCK_REVIEW: ReviewCheck = {
  ready: true,
  invalidPages: [],
  fieldMessages: {},
  InvalidPagesList: () => <></>,
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

export const mockGetStatus = (
  modifiers: Partial<
    Pick<getExperiment_experimentBySlug, "status" | "publishStatus">
  >,
) => {
  const { experiment } = mockExperimentQuery("boo", modifiers);
  return getStatus(experiment);
};

const fiveDaysAgo = new Date();
fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);

/** Creates a single mock experiment suitable for getAllExperiments queries.  */
export function mockSingleDirectoryExperiment(
  overrides: Partial<getAllExperiments_experiments> = {},
  slugIndex: number = Math.round(Math.random() * 100),
): getAllExperiments_experiments {
  return {
    slug: `some-experiment-${slugIndex}`,
    owner: {
      username: "example@mozilla.com",
    },
    monitoringDashboardUrl:
      "https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=bug-1668861-pref-measure-set-to-default-adoption-impact-of-chang-release-81-83",
    name: "Open-architected background installation",
    status: NimbusExperimentStatus.COMPLETE,
    publishStatus: NimbusExperimentPublishStatus.IDLE,
    featureConfig: {
      slug: "newtab",
      name: "New tab",
    },
    proposedEnrollment: 7,
    proposedDuration: 28,
    startDate: fiveDaysAgo.toISOString(),
    computedEndDate: new Date(Date.now() + 12096e5).toISOString(),
    isEndRequested: false,
    resultsReady: false,
    ...overrides,
  };
}

export function mockDirectoryExperiments(
  overrides: Partial<getAllExperiments_experiments>[] = [
    {
      status: NimbusExperimentStatus.DRAFT,
      startDate: null,
      computedEndDate: null,
    },
    {
      status: NimbusExperimentStatus.PREVIEW,
      computedEndDate: null,
    },
    {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
      computedEndDate: null,
    },
    {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      computedEndDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      computedEndDate: null,
    },
    {
      status: NimbusExperimentStatus.LIVE,
      computedEndDate: null,
    },
    {
      status: NimbusExperimentStatus.COMPLETE,
    },
    {
      status: NimbusExperimentStatus.DRAFT,
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
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

// Basically the same as useOutcomes, but uses the mocked config values
export function mockOutcomeSets(experiment: getExperiment_experimentBySlug): {
  primaryOutcomes: OutcomesList;
  secondaryOutcomes: OutcomesList;
} {
  const { outcomes } = MOCK_CONFIG;

  const pairOutcomes = (slugs: OutcomeSlugs) => {
    if (!slugs || !outcomes) {
      return [];
    }

    return slugs
      .map((slug) => outcomes!.find((outcome) => outcome!.slug === slug))
      .filter((outcome) => outcome != null);
  };

  return {
    primaryOutcomes: pairOutcomes(experiment.primaryOutcomes),
    secondaryOutcomes: pairOutcomes(experiment.secondaryOutcomes),
  };
}

// HACK: treat rejection as the superset changelog type since we don't
// actually have the generic type in auto-generated types
export type NimbusChangeLog = getExperiment_experimentBySlug["rejection"];
export type NimbusUser = getExperiment_experimentBySlug_rejection_changedBy;

export const mockUser = (email = "abc@mozilla.com"): NimbusUser => ({
  email,
});

export const mockChangelog = (
  email = "abc@mozilla.com",
  message: string | null = null,
  changedOn: DateTime = new Date().toISOString(),
): NimbusChangeLog => ({
  changedBy: mockUser(email),
  changedOn,
  message,
});
