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
import React, { ReactNode } from "react";
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
  NimbusChangeLogOldStatus,
  NimbusChangeLogOldStatusNext,
  NimbusDocumentationLinkTitle,
  NimbusExperimentApplicationEnum,
  NimbusExperimentChannelEnum,
  NimbusExperimentFirefoxVersionEnum,
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../types/globalTypes";
import { ResultsContext } from "./contexts";
import { getStatus } from "./experiment";
import { OutcomesList, OutcomeSlugs } from "./types";
import { mockAnalysis } from "./visualization/mocks";
import { AnalysisData } from "./visualization/types";
import { getSortedBranchNames } from "./visualization/utils";

export interface MockedProps {
  config?: Partial<typeof MOCK_CONFIG> | null;
  childProps?: Record<any, any>;
  children?: React.ReactElement;
  mocks?: MockedResponse<Record<string, any>>[];
  addTypename?: boolean;
  link?: ApolloLink;
}

export interface MockedState {
  client: ApolloClient<any>;
}

export const MOCK_CONFIG: getConfig_nimbusConfig = {
  applications: [
    {
      label: "Desktop",
      value: NimbusExperimentApplicationEnum.DESKTOP,
    },
    {
      label: "Toaster",
      value: "TOASTER",
    },
    {
      label: "iOS",
      value: NimbusExperimentApplicationEnum.IOS,
    },
    {
      label: "Android",
      value: NimbusExperimentApplicationEnum.FENIX,
    },
  ],
  channels: [
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
  conclusionRecommendations: [
    { label: "Rerun", value: "RERUN" },
    {
      label: "Graduate",
      value: "GRADUATE",
    },
    {
      label: "Change course",
      value: "CHANGE_COURSE",
    },
    { label: "Stop", value: "STOP" },
    {
      label: "Run follow ups",
      value: "FOLLOWUP",
    },
  ],
  applicationConfigs: [
    {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channels: [
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
    },
    {
      application: NimbusExperimentApplicationEnum.FENIX,
      channels: [
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
    },
    {
      application: NimbusExperimentApplicationEnum.IOS,
      channels: [
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
    },
  ],
  allFeatureConfigs: [
    {
      id: 1,
      name: "Picture-in-Picture",
      slug: "picture-in-picture",
      description:
        "Quickly above also mission action. Become thing item institution plan.\nImpact friend wonder. Interview strategy nature question. Admit room without impact its enter forward.",
      application: NimbusExperimentApplicationEnum.FENIX,
      ownerEmail: "sheila43@yahoo.com",
      schema: null,
    },
    {
      id: 2,
      name: "Mauris odio erat",
      slug: "mauris-odio-erat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusExperimentApplicationEnum.DESKTOP,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
    {
      id: 3,
      name: "Foo lila sat (iOS)",
      slug: "foo-lila-sat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusExperimentApplicationEnum.IOS,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
    {
      id: 4,
      name: "Foo lila sat (Android)",
      slug: "foo-lila-sat",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      application: NimbusExperimentApplicationEnum.FENIX,
      ownerEmail: "dude23@yahoo.com",
      schema: '{ "sample": "schema" }',
    },
  ],
  firefoxVersions: [
    {
      label: "Firefox 80",
      value: "FIREFOX_83",
    },
    {
      label: "Firefox 16",
      value: "FIREFOX_16",
    },
    {
      label: "Firefox 32",
      value: "FIREFOX_32",
    },
    {
      label: "Firefox 64",
      value: "FIREFOX_64",
    },
  ],
  outcomes: [
    {
      friendlyName: "Picture-in-Picture",
      slug: "picture_in_picture",
      application: NimbusExperimentApplicationEnum.DESKTOP,
      description: "foo",
      isDefault: true,
      metrics: [
        {
          slug: "picture_in_picture",
          friendlyName: "Picture-in-Picture",
          description: "Test",
        },
      ],
    },
    {
      friendlyName: "Feature B",
      slug: "feature_b",
      application: NimbusExperimentApplicationEnum.DESKTOP,
      description: "bar",
      isDefault: false,
      metrics: [
        {
          slug: "feature_b",
          friendlyName: "Feature B",
          description: "Test",
        },
      ],
    },
    {
      friendlyName: "Feature C",
      slug: "feature_c",
      application: NimbusExperimentApplicationEnum.DESKTOP,
      description: "baz",
      isDefault: false,
      metrics: [
        {
          slug: "feature_c",
          friendlyName: "Feature C",
          description: "Test",
        },
      ],
    },
    {
      friendlyName: "Feature No Data",
      slug: "feature_nodata",
      application: NimbusExperimentApplicationEnum.DESKTOP,
      description: "meep",
      isDefault: false,
      metrics: [
        {
          slug: "feature_nodata",
          friendlyName: "Feature No Data",
          description: "Test",
        },
      ],
    },
    {
      friendlyName: "Feature D",
      slug: "feature_d",
      application: NimbusExperimentApplicationEnum.FENIX,
      description: "feature_d",
      isDefault: false,
      metrics: [
        {
          slug: "uri_count",
          friendlyName: "Feature D",
          description: "Test",
        },
      ],
    },
  ],
  owners: [
    { username: "alpha-example@mozilla.com" },
    { username: "beta-example@mozilla.com" },
    { username: "gamma-example@mozilla.com" },
  ],
  targetingConfigs: [
    {
      label: "Mac Only",
      value: "MAC_ONLY",
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
  locales: [
    {
      name: "Acholi",
      id: 1,
    },
    {
      name: "Afrikaans",
      id: 2,
    },
    {
      name: "Albanian",
      id: 3,
    },
  ],
  countries: [
    {
      name: "Eritrea",
      id: 1,
    },
    {
      name: "Estonia",
      id: 2,
    },
    {
      name: "Eswatini",
      id: 3,
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

export const MOCK_EXPERIMENT: Partial<getExperiment["experimentBySlug"]> = {
  id: 1,
  isArchived: false,
  canEdit: true,
  canArchive: true,
  owner: {
    email: "example@mozilla.com",
  },
  name: "Open-architected background installation",
  slug: "open-architected-background-installation",
  status: NimbusExperimentStatusEnum.DRAFT,
  statusNext: null,
  publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
  monitoringDashboardUrl: "https://mozilla.cloud.looker.com",
  hypothesis: "Realize material say pretty.",
  application: NimbusExperimentApplicationEnum.DESKTOP,
  publicDescription: "Official approach present industry strategy dream piece.",
  referenceBranch: {
    id: 123,
    name: "User-centric mobile solution",
    slug: "control",
    description: "Behind almost radio result personal none future current.",
    ratio: 1,
    featureValue: '{"environmental-fact": "really-citizen"}',
    featureEnabled: true,
    screenshots: [],
  },
  featureConfigs: [],
  treatmentBranches: [
    {
      id: 456,
      name: "Managed zero tolerance projection",
      slug: "treatment",
      description: "Next ask then he in degree order.",
      ratio: 1,
      featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
      featureEnabled: true,
      screenshots: [],
    },
  ],
  primaryOutcomes: ["picture_in_picture", "feature_c", "feature_nodata"],
  secondaryOutcomes: ["feature_b"],
  channel: NimbusExperimentChannelEnum.NIGHTLY,
  firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_16,
  firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_64,
  targetingConfigSlug: "MAC_ONLY",
  jexlTargetingExpression: "localeLanguageCode == 'en' && region == 'US'",
  populationPercent: "40",
  totalEnrolledClients: 68000,
  proposedEnrollment: 1,
  proposedDuration: 28,
  readyForReview: {
    ready: true,
    message: {},
    warnings: {},
  },
  signoffRecommendations: {
    qaSignoff: true,
    vpSignoff: false,
    legalSignoff: false,
  },
  startDate: new Date().toISOString(),
  computedEndDate: new Date(Date.now() + 12096e5).toISOString(),
  computedDurationDays: 14,
  computedEnrollmentDays: 1,
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
  reviewUrl:
    "https://kinto.example.com/v1/admin/#/buckets/main-workspace/collections/nimbus-desktop-experiments/simple-review",
  locales: [{ name: "Quebecois", id: 1 }],
  countries: [{ name: "Canada", id: 1 }],
};

export function mockExperiment<
  T extends getExperiment["experimentBySlug"] = getExperiment_experimentBySlug,
>(modifications: Partial<getExperiment["experimentBySlug"]> = {}): T {
  return Object.assign({}, MOCK_EXPERIMENT, modifications) as T;
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
  fieldWarnings: {},
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
    Pick<
      getExperiment_experimentBySlug,
      | "status"
      | "publishStatus"
      | "statusNext"
      | "isEnrollmentPausePending"
      | "isArchived"
    >
  >,
) => {
  const { experiment } = mockExperimentQuery("boo", modifiers);
  return getStatus(experiment);
};

/** Creates a single mock experiment suitable for getAllExperiments queries.  */
export function mockSingleDirectoryExperiment(
  overrides: Partial<getAllExperiments_experiments> = {},
  slugIndex: number = Math.round(Math.random() * 100),
): getAllExperiments_experiments {
  const now = Date.now();
  const oneDay = 1000 * 60 * 60 * 24;
  const startTime = now - oneDay * 60 - 21 * oneDay * Math.random();
  const endTime = now - oneDay * 30 + 21 * oneDay * Math.random();

  return {
    isArchived: false,
    slug: `some-experiment-${slugIndex}`,
    owner: {
      username: "example@mozilla.com",
    },
    application: MOCK_CONFIG.applications![0]!
      .value as NimbusExperimentApplicationEnum,
    firefoxMinVersion: MOCK_CONFIG.firefoxVersions![0]!
      .value as NimbusExperimentFirefoxVersionEnum,
    firefoxMaxVersion: MOCK_CONFIG.firefoxVersions![3]!
      .value as NimbusExperimentFirefoxVersionEnum,
    monitoringDashboardUrl:
      "https://mozilla.cloud.looker.com/dashboards-next/216?Experiment=bug-1668861-pref-measure-set-to-default-adoption-impact-of-chang-release-81-83",
    name: "Open-architected background installation",
    status: NimbusExperimentStatusEnum.COMPLETE,
    statusNext: null,
    publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
    featureConfig: MOCK_CONFIG.allFeatureConfigs![0],
    featureConfigs: [MOCK_CONFIG.allFeatureConfigs![0]],
    isEnrollmentPaused: false,
    isEnrollmentPausePending: false,
    proposedEnrollment: 7,
    proposedDuration: 28,
    startDate: new Date(startTime).toISOString(),
    computedEndDate: new Date(endTime).toISOString(),
    resultsReady: false,
    ...overrides,
  };
}

export function mockDirectoryExperiments(
  overrides: Partial<getAllExperiments_experiments>[] = [
    {
      name: "Lorem ipsum dolor sit amet",
      status: NimbusExperimentStatusEnum.DRAFT,
      owner: { username: "alpha-example@mozilla.com" },
      startDate: null,
      computedEndDate: null,
    },
    {
      name: "Ipsum dolor sit amet",
      status: NimbusExperimentStatusEnum.DRAFT,
      owner: { username: "gamma-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![0]],
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      startDate: null,
      computedEndDate: null,
    },
    {
      name: "Dolor sit amet",
      status: NimbusExperimentStatusEnum.DRAFT,
      owner: { username: "beta-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
      startDate: null,
      computedEndDate: null,
    },
    {
      name: "Consectetur adipiscing elit",
      status: NimbusExperimentStatusEnum.PREVIEW,
      owner: { username: "alpha-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![2]],
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      computedEndDate: null,
    },
    {
      name: "Aliquam interdum ac lacus at dictum",
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      owner: { username: "beta-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![0]],
      computedEndDate: null,
    },
    {
      name: "Nam semper sit amet orci in imperdiet",
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      owner: { username: "gamma-example@mozilla.com" },
    },
    {
      name: "Duis ornare mollis sem.",
      status: NimbusExperimentStatusEnum.LIVE,
      owner: { username: "alpha-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
    },
    {
      name: "Nec suscipit mi accumsan id",
      status: NimbusExperimentStatusEnum.LIVE,
      owner: { username: "beta-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![2]],
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      resultsReady: true,
    },
    {
      name: "Etiam congue risus quis aliquet eleifend",
      status: NimbusExperimentStatusEnum.LIVE,
      owner: { username: "gamma-example@mozilla.com" },
    },
    {
      name: "Nam gravida",
      status: NimbusExperimentStatusEnum.COMPLETE,
      owner: { username: "alpha-example@mozilla.com" },
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![0]],
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      resultsReady: false,
    },
    {
      name: "Quam quis volutpat ornare",
      status: NimbusExperimentStatusEnum.DRAFT,
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
      owner: { username: "beta-example@mozilla.com" },
    },
    {
      name: "Lorem arcu faucibus tortor",
      featureConfigs: null,
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      owner: { username: "gamma-example@mozilla.com" },
    },
    {
      isArchived: true,
      name: "Archived Experiment",
      featureConfigs: null,
      application: MOCK_CONFIG.applications![1]!
        .value as NimbusExperimentApplicationEnum,
      owner: { username: "gamma-example@mozilla.com" },
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
  oldStatus: NimbusChangeLogOldStatus.LIVE,
  oldStatusNext: null,
  changedBy: mockUser(email),
  changedOn,
  message,
});

export const mockRejectionChangelog = (
  email = "abc@mozilla.com",
  message: string | null = null,
  oldStatus: NimbusChangeLogOldStatus = NimbusChangeLogOldStatus.LIVE,
  oldStatusNext: NimbusChangeLogOldStatusNext | null = null,
  changedOn: DateTime = new Date().toISOString(),
): NimbusChangeLog => ({
  oldStatus,
  oldStatusNext,
  changedBy: mockUser(email),
  changedOn,
  message,
});

export const MockResultsContextProvider = ({
  children,
  analysis = mockAnalysis(),
}: {
  children: ReactNode;
  analysis?: AnalysisData;
}) => {
  const sortedBranchNames = getSortedBranchNames(analysis);
  const value = {
    analysis,
    sortedBranchNames,
    controlBranchName: sortedBranchNames[0],
  };

  return (
    <ResultsContext.Provider {...{ value }}>{children}</ResultsContext.Provider>
  );
};
