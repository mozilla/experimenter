/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import React from "react";
import selectEvent from "react-select-event";
import {
  filterAndSortTargetingConfigs,
  MOBILE_APPLICATIONS,
} from "src/components/PageEditAudience/FormAudience";
import {
  MOCK_EXPERIMENT,
  MOCK_ROLLOUT,
  Subject,
} from "src/components/PageEditAudience/FormAudience/mocks";
import { snakeToCamelCase } from "src/lib/caseConversions";
import {
  EXTERNAL_URLS,
  FIELD_MESSAGES,
  TOOLTIP_DURATION,
} from "src/lib/constants";
import {
  mockDirectoryExperiments,
  mockExperimentQuery,
  MOCK_CONFIG,
  MOCK_EXPERIMENTS_BY_APPLICATION,
} from "src/lib/mocks";
import { assertSerializerMessages } from "src/lib/test-utils";
import { getAllExperimentsByApplication_experimentsByApplication } from "src/types/getAllExperimentsByApplication";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentApplicationEnum,
  NimbusExperimentChannelEnum,
  NimbusExperimentFirefoxVersionEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

describe("FormAudience", () => {
  const origWindowOpen = global.window.open;
  let mockWindowOpen: any;

  beforeEach(() => {
    mockWindowOpen = jest.fn();
    global.window.open = mockWindowOpen;
  });

  afterEach(() => {
    global.window.open = origWindowOpen;
  });

  describe("excluded and required experiments fields", () => {
    const sum = (items: number[]) =>
      items.reduce((acc: number, curr: number) => acc + curr);
    const countBranches = (
      experiments: getAllExperimentsByApplication_experimentsByApplication[],
    ) => sum(experiments.map((e) => e.treatmentBranches!.length + 2));
    const query = (field: string) =>
      `#react-select-${field}-listbox .react-select__option`;

    it("fields renders options", async () => {
      const experiment = {
        ...MOCK_EXPERIMENT,
        name: MOCK_EXPERIMENTS_BY_APPLICATION[0].name,
        slug: MOCK_EXPERIMENTS_BY_APPLICATION[0].slug,
        id: MOCK_EXPERIMENTS_BY_APPLICATION[0].id,
      };

      const { container } = render(<Subject experiment={experiment} />);
      const excluded = screen.getByLabelText(/Exclude users enrolled/);

      let options = container.querySelectorAll(query("excludedExperiments"));
      expect(options.length).toEqual(0);
      await selectEvent.openMenu(excluded);
      options = container.querySelectorAll(query("excludedExperiments"));
      expect(options.length).toEqual(
        countBranches(MOCK_EXPERIMENTS_BY_APPLICATION) - 3,
      );

      expect(
        Array.from(options, (e) => e.textContent).find((text) =>
          text?.includes(`(${experiment.slug})`),
        ),
      ).toBeUndefined();

      const required = screen.getByLabelText(/Require users to be enrolled/);
      options = container.querySelectorAll(query("requiredExperiments"));
      expect(options.length).toEqual(0);
      await selectEvent.openMenu(required);
      options = container.querySelectorAll(query("requiredExperiments"));
      expect(options.length).toEqual(
        countBranches(MOCK_EXPERIMENTS_BY_APPLICATION) - 3,
      );

      expect(
        Array.from(options, (e) => e.textContent).find((text) =>
          text?.includes(`(${experiment.slug})`),
        ),
      ).toBeUndefined();
    });

    it("only displays one option for experiments with one branch", async () => {
      const experiment = {
        ...MOCK_EXPERIMENT,
        name: MOCK_EXPERIMENTS_BY_APPLICATION[0].name,
        slug: MOCK_EXPERIMENTS_BY_APPLICATION[0].slug,
        id: MOCK_EXPERIMENTS_BY_APPLICATION[0].id,
      };

      const experimentsByApplication = [
        { ...MOCK_EXPERIMENTS_BY_APPLICATION[1], treatmentBranches: [] },
      ];

      const { container } = render(
        <Subject
          experiment={experiment}
          experimentsByApplication={{
            allExperiments: experimentsByApplication,
          }}
        />,
      );
      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);
      let options = container.querySelectorAll(query("excludedExperiments"));
      expect(options.length).toEqual(1);

      expect(
        Array.from(options, (e) => e.textContent).find((text) =>
          text?.includes(`(${experiment.slug})`),
        ),
      ).toBeUndefined();

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      options = container.querySelectorAll(query("requiredExperiments"));
      expect(options.length).toEqual(1);

      expect(
        Array.from(options, (e) => e.textContent).find((text) =>
          text?.includes(`(${experiment.slug})`),
        ),
      ).toBeUndefined();
    });

    it("saves required and excluded experiments with all branches for experiments", async () => {
      const onSubmit = jest.fn();
      const MOCK_EXPERIMENTS_BY_APPLICATION: getAllExperimentsByApplication_experimentsByApplication[] =
        Array.from(mockDirectoryExperiments().entries()).map(
          ([idx, experiment]) => ({
            id: idx + 1,
            name: experiment.name,
            slug:
              experiment.slug ??
              experiment.name.toLowerCase().replace(" ", "-"),
            publicDescription: "mock description",
            referenceBranch: { slug: "control" },
            treatmentBranches: [{ slug: "treatment" }],
          }),
        );
      const experiment: getExperiment_experimentBySlug = mockExperimentQuery(
        "demo-slug",
        {
          excludedExperimentsBranches: [],
          requiredExperimentsBranches: [],
        },
      ).experiment;
      const requiredExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];
      const excludedExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[2];

      const expected: ExperimentInput = {
        channel: experiment.channel,
        firefoxMinVersion: experiment.firefoxMinVersion,
        firefoxMaxVersion: experiment.firefoxMaxVersion,
        targetingConfigSlug: experiment.targetingConfigSlug,
        populationPercent: experiment.populationPercent,
        totalEnrolledClients: experiment.totalEnrolledClients,
        proposedEnrollment: "" + experiment.proposedEnrollment,
        proposedDuration: "" + experiment.proposedDuration,
        countries: experiment.countries.map((v) => "" + v.id),
        locales: experiment.locales.map((v) => "" + v.id),
        languages: experiment.languages.map((v) => "" + v.id),
        isSticky: experiment.isSticky,
        isFirstRun: experiment.isFirstRun,
        requiredExperimentsBranches: [
          {
            requiredExperiment: requiredExperiment.id,
            branchSlug: null,
          },
        ],
        excludedExperimentsBranches: [
          {
            excludedExperiment: excludedExperiment.id,
            branchSlug: null,
          },
        ],
      };

      render(<Subject {...{ experiment, onSubmit }} />);
      await screen.findByTestId("FormAudience");

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      await selectEvent.select(required, [
        `${requiredExperiment.name} (All branches)`,
      ]);

      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);
      await selectEvent.select(excluded, [
        `${excludedExperiment.name} (All branches)`,
      ]);

      const submitButton = screen.getByTestId("submit-button");

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        expect(onSubmit.mock.calls).toEqual([[expected, false]]);
      });
    });

    it("saves required and excluded experiments with all branches for rollouts", async () => {
      const onSubmit = jest.fn();
      const MOCK_EXPERIMENTS_BY_APPLICATION: getAllExperimentsByApplication_experimentsByApplication[] =
        Array.from(mockDirectoryExperiments().entries()).map(
          ([idx, experiment]) => ({
            id: idx + 1,
            name: experiment.name,
            slug:
              experiment.slug ??
              experiment.name.toLowerCase().replace(" ", "-"),
            publicDescription: "mock description",
            referenceBranch: { slug: "control" },
            treatmentBranches: [{ slug: "treatment" }],
          }),
        );
      const experiment: getExperiment_experimentBySlug = mockExperimentQuery(
        "demo-slug",
        {
          isRollout: true,
          excludedExperimentsBranches: [],
          requiredExperimentsBranches: [],
        },
      ).experiment;
      const requiredExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];
      const excludedExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[2];

      const expected: ExperimentInput = {
        channel: experiment.channel,
        firefoxMinVersion: experiment.firefoxMinVersion,
        firefoxMaxVersion: experiment.firefoxMaxVersion,
        targetingConfigSlug: experiment.targetingConfigSlug,
        populationPercent: experiment.populationPercent,
        totalEnrolledClients: experiment.totalEnrolledClients,
        proposedEnrollment: "" + experiment.proposedEnrollment,
        proposedDuration: "" + experiment.proposedDuration,
        countries: experiment.countries.map((v) => "" + v.id),
        locales: experiment.locales.map((v) => "" + v.id),
        languages: experiment.languages.map((v) => "" + v.id),
        isSticky: experiment.isSticky,
        isFirstRun: experiment.isFirstRun,
        requiredExperimentsBranches: [
          {
            requiredExperiment: requiredExperiment.id,
            branchSlug: null,
          },
        ],
        excludedExperimentsBranches: [
          {
            excludedExperiment: excludedExperiment.id,
            branchSlug: null,
          },
        ],
      };

      render(<Subject {...{ experiment, onSubmit }} />);
      await screen.findByTestId("FormAudience");

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      await selectEvent.select(required, [
        `${requiredExperiment.name} (All branches)`,
      ]);

      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);
      await selectEvent.select(excluded, [
        `${excludedExperiment.name} (All branches)`,
      ]);

      const submitButton = screen.getByTestId("submit-button");

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        expect(onSubmit.mock.calls).toEqual([[expected, false]]);
      });
    });

    it("saves required and excluded experiments with specific branches for experiments", async () => {
      const onSubmit = jest.fn();
      const MOCK_EXPERIMENTS_BY_APPLICATION: getAllExperimentsByApplication_experimentsByApplication[] =
        Array.from(mockDirectoryExperiments().entries()).map(
          ([idx, experiment]) => ({
            id: idx + 1,
            name: experiment.name,
            slug:
              experiment.slug ??
              experiment.name.toLowerCase().replace(" ", "-"),
            publicDescription: "mock description",
            referenceBranch: { slug: "control" },
            treatmentBranches: [{ slug: "treatment" }],
          }),
        );
      const experiment: getExperiment_experimentBySlug = mockExperimentQuery(
        "demo-slug",
        {
          excludedExperimentsBranches: [],
          requiredExperimentsBranches: [],
        },
      ).experiment;
      const requiredExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];
      const excludedExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[2];

      const expected: ExperimentInput = {
        channel: experiment.channel,
        firefoxMinVersion: experiment.firefoxMinVersion,
        firefoxMaxVersion: experiment.firefoxMaxVersion,
        targetingConfigSlug: experiment.targetingConfigSlug,
        populationPercent: experiment.populationPercent,
        totalEnrolledClients: experiment.totalEnrolledClients,
        proposedEnrollment: "" + experiment.proposedEnrollment,
        proposedDuration: "" + experiment.proposedDuration,
        countries: experiment.countries.map((v) => "" + v.id),
        locales: experiment.locales.map((v) => "" + v.id),
        languages: experiment.languages.map((v) => "" + v.id),
        isSticky: experiment.isSticky,
        isFirstRun: experiment.isFirstRun,
        requiredExperimentsBranches: [
          {
            requiredExperiment: requiredExperiment.id,
            branchSlug: "control",
          },
        ],
        excludedExperimentsBranches: [
          {
            excludedExperiment: excludedExperiment.id,
            branchSlug: "treatment",
          },
        ],
      };

      render(<Subject {...{ experiment, onSubmit }} />);
      await screen.findByTestId("FormAudience");

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      await selectEvent.select(required, [
        `${requiredExperiment.name} (control branch)`,
      ]);

      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);
      await selectEvent.select(excluded, [
        `${excludedExperiment.name} (treatment branch)`,
      ]);

      const submitButton = screen.getByTestId("submit-button");

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        expect(onSubmit.mock.calls).toEqual([[expected, false]]);
      });
    });

    it("saves required and excluded experiments with specific branches for rollouts", async () => {
      const onSubmit = jest.fn();
      const MOCK_EXPERIMENTS_BY_APPLICATION: getAllExperimentsByApplication_experimentsByApplication[] =
        Array.from(mockDirectoryExperiments().entries()).map(
          ([idx, experiment]) => ({
            id: idx + 1,
            name: experiment.name,
            slug:
              experiment.slug ??
              experiment.name.toLowerCase().replace(" ", "-"),
            publicDescription: "mock description",
            referenceBranch: { slug: "control" },
            treatmentBranches: [{ slug: "treatment" }],
          }),
        );
      const experiment: getExperiment_experimentBySlug = mockExperimentQuery(
        "demo-slug",
        {
          isRollout: true,
          excludedExperimentsBranches: [],
          requiredExperimentsBranches: [],
        },
      ).experiment;
      const requiredExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];
      const excludedExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[2];

      const expected: ExperimentInput = {
        channel: experiment.channel,
        firefoxMinVersion: experiment.firefoxMinVersion,
        firefoxMaxVersion: experiment.firefoxMaxVersion,
        targetingConfigSlug: experiment.targetingConfigSlug,
        populationPercent: experiment.populationPercent,
        totalEnrolledClients: experiment.totalEnrolledClients,
        proposedEnrollment: "" + experiment.proposedEnrollment,
        proposedDuration: "" + experiment.proposedDuration,
        countries: experiment.countries.map((v) => "" + v.id),
        locales: experiment.locales.map((v) => "" + v.id),
        languages: experiment.languages.map((v) => "" + v.id),
        isSticky: experiment.isSticky,
        isFirstRun: experiment.isFirstRun,
        requiredExperimentsBranches: [
          {
            requiredExperiment: requiredExperiment.id,
            branchSlug: "control",
          },
        ],
        excludedExperimentsBranches: [
          {
            excludedExperiment: excludedExperiment.id,
            branchSlug: "treatment",
          },
        ],
      };

      render(<Subject {...{ experiment, onSubmit }} />);
      await screen.findByTestId("FormAudience");

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      await selectEvent.select(required, [
        `${requiredExperiment.name} (control branch)`,
      ]);

      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);
      await selectEvent.select(excluded, [
        `${excludedExperiment.name} (treatment branch)`,
      ]);

      const submitButton = screen.getByTestId("submit-button");

      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        expect(onSubmit.mock.calls).toEqual([[expected, false]]);
      });
    });

    it("filters selected required experiment branches from the exclude field options", async () => {
      const experiment = {
        ...MOCK_EXPERIMENT,
        name: MOCK_EXPERIMENTS_BY_APPLICATION[0].name,
        slug: MOCK_EXPERIMENTS_BY_APPLICATION[0].slug,
        id: MOCK_EXPERIMENTS_BY_APPLICATION[0].id,
        excludedExperimentsBranches: [],
        requiredExperimentsBranches: [],
      };
      const requiredExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];

      const { container } = render(<Subject experiment={experiment} />);
      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);
      await selectEvent.select(required, [
        `${requiredExperiment.name} (All branches)`,
      ]);

      const excluded = screen.getByLabelText(/Exclude users enrolled/);
      await selectEvent.openMenu(excluded);

      const options = container.querySelectorAll(query("excludedExperiments"));

      expect(options.length).toEqual(
        countBranches(MOCK_EXPERIMENTS_BY_APPLICATION) - 6,
      );
      [experiment, requiredExperiment].forEach((filteredExperiment) => {
        expect(
          Array.from(options, (e) => e.textContent).filter((text) =>
            text?.includes(filteredExperiment.slug),
          ).length,
        ).toEqual(0);
      });
    });

    it("filters selected excluded experiment branch from the required field options", async () => {
      const experiment = {
        ...MOCK_EXPERIMENT,
        name: MOCK_EXPERIMENTS_BY_APPLICATION[0].name,
        slug: MOCK_EXPERIMENTS_BY_APPLICATION[0].slug,
        id: MOCK_EXPERIMENTS_BY_APPLICATION[0].id,
        excludedExperimentsBranches: [],
        requiredExperimentsBranches: [],
      };
      const excludedExperiment = MOCK_EXPERIMENTS_BY_APPLICATION[1];

      const { container } = render(<Subject experiment={experiment} />);
      const excluded = screen.getByLabelText(/Exclude users enrolled/);

      await selectEvent.openMenu(excluded);
      await selectEvent.select(excluded, [
        `${excludedExperiment.name} (All branches)`,
      ]);

      const required = screen.getByLabelText(/Require users to be enrolled/);
      await selectEvent.openMenu(required);

      const options = container.querySelectorAll(query("requiredExperiments"));

      expect(options.length).toEqual(
        countBranches(MOCK_EXPERIMENTS_BY_APPLICATION) - 6,
      );
      [experiment, excludedExperiment].forEach((filteredExperiment) => {
        expect(
          Array.from(options, (e) => e.textContent).filter((text) =>
            text?.includes(filteredExperiment.slug),
          ).length,
        ).toEqual(0);
      });
    });
  });

  it("renders without error", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isSticky: true,
          isFirstRun: true,
        }}
        config={{
          ...MOCK_CONFIG,
          channels: [
            { label: "Nightly", value: "NIGHTLY" },
            { label: "Release", value: "RELEASE" },
          ],
          applicationConfigs: [
            {
              application: NimbusExperimentApplicationEnum.DESKTOP,
              channels: [{ label: "Nightly", value: "NIGHTLY" }],
            },
          ],
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    expect(screen.getByTestId("learn-more-link")).toHaveAttribute(
      "href",
      EXTERNAL_URLS.WORKFLOW_MANA_DOC,
    );
    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;
    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![0]!.value,
    );

    // Assert that the targeting choices are filtered for application
    expect(
      Array.from(targetingConfigSlug.options).map((node) => node.value),
    ).toEqual(["", "MAC_ONLY"]);

    // Assert that we have only the application channels available
    expect(screen.getByText("Nightly")).toBeInTheDocument();
    expect(screen.queryByText("Release")).not.toBeInTheDocument();

    expect(
      await screen.findByTestId("tooltip-duration-audience"),
    ).toHaveAttribute("data-tip", TOOLTIP_DURATION);

    expect(screen.getByTestId("locales")).toHaveTextContent(
      MOCK_EXPERIMENT.locales[0]!.name!,
    );

    expect(screen.getByTestId("countries")).toHaveTextContent(
      MOCK_EXPERIMENT.countries[0]!.name!,
    );

    expect(screen.getByTestId("isSticky")).toBeChecked();
    expect(screen.queryByText("First Run Experiment")).not.toBeInTheDocument();
  });

  it("expect sticky enrollment to be not selected as sticky is not required for the selected targeting", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isSticky: false,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;
    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![0]!.value,
    );

    expect(screen.getByTestId("isSticky")).not.toBeChecked();
  });

  it("expect sticky enrollment to be selected as sticky is required for the selected targeting", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          targetingConfigSlug: "WIN_ONLY",
          targetingConfig: [
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
          ],
          isSticky: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;

    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![1]!.value,
    );
    expect(screen.getByTestId("isSticky")).toHaveProperty("checked", true);
    expect(screen.getByTestId("isSticky")).toBeDisabled();
    await expect(
      screen.getByTestId("sticky-required-warning"),
    ).toBeInTheDocument();
  });

  it("expect desktop version warning when under 114", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_ROLLOUT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          status: NimbusExperimentStatusEnum.DRAFT,
          isRollout: true,
          isSticky: true,
          firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_107,
        }}
      />,
    );
    screen.queryByText("WARNING", { selector: `[data-for=firefoxMinVersion]` });
  });

  it("expect no desktop version warning when over 114", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_ROLLOUT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          status: NimbusExperimentStatusEnum.DRAFT,
          isRollout: true,
          isSticky: true,
          firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_118,
        }}
      />,
    );
    screen.queryByText("", { selector: `[data-for=firefoxMinVersion]` });
  });

  it("expect sticky enrollment to be optional as changing targeting from sticky required to sticky not required", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          targetingConfigSlug: "WIN_ONLY",
          targetingConfig: [
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
          ],
          isSticky: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;

    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![1]!.value,
    );
    fireEvent.change(screen.getByTestId("targetingConfigSlug"), {
      target: { value: MOCK_CONFIG!.targetingConfigs![0]!.value },
    });
    fireEvent.click(screen.getByTestId("isSticky"), {
      target: { checked: false },
    });
    expect(screen.getByTestId("isSticky")).toHaveProperty("checked", true);
    expect(screen.getByTestId("isSticky")).not.toBeDisabled();
    await expect(
      screen.queryByTestId("sticky-required-warning"),
    ).not.toBeInTheDocument();
  });

  it("sticky enrollment doesn't change by modifying the other fields value", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isSticky: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId("isSticky")).toBeChecked();
    for (const fieldName of [
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.change(field, { target: { value: "123" } });
        fireEvent.blur(field);
      });
      expect(screen.getByTestId("isSticky")).toBeChecked();
    }

    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: "23" } });
    });

    expect(screen.getByTestId("isSticky")).toBeChecked();
  });

  it("sticky enrollment doesn't change when clicking save or save and continue", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isSticky: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId("isSticky")).toBeChecked();

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(screen.getByTestId("isSticky")).toBeChecked();

    const submitandContinueButton = screen.getByTestId("next-button");
    await act(async () => {
      fireEvent.click(submitandContinueButton);
    });
    expect(screen.getByTestId("isSticky")).toBeChecked();
  });

  it("expect first run to be selected as first run is required for the selected targeting", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          targetingConfigSlug: "MOBILE_ONLY",
          targetingConfig: [
            {
              label: "Mobile Only",
              value: "MOBILE_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.FENIX],
              description: "Mobile only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
          ],
          isSticky: true,
          isFirstRun: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mobile Only",
              value: "MOBILE_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.FENIX],
              description: "Mobile only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
          ],
        }}
      />,
    );

    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;

    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![2]!.value,
    );
    expect(screen.getByTestId("isFirstRun")).toHaveProperty("checked", true);
    expect(screen.getByTestId("isFirstRun")).toBeDisabled();
    await expect(
      screen.getByTestId("is-first-run-required-warning"),
    ).toBeInTheDocument();
  });
  it("expect first run not to be present in desktop as it is not required for selected targeting", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          targetingConfigSlug: "WIN_ONLY",
          targetingConfig: [
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
          ],
          isSticky: true,
          isFirstRun: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
          ],
        }}
      />,
    );

    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;

    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![1]!.value,
    );
    expect(screen.queryByText("First Run Experiment")).not.toBeInTheDocument();
  });

  it("expect sticky enrollment to be optional as changing targeting from sticky required to sticky not required", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          targetingConfigSlug: "MOBILE_ONLY",
          targetingConfig: [
            {
              label: "Mobile Only",
              value: "MOBILE_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.FENIX],
              description: "Mobile only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
          ],
          isSticky: true,
          isFirstRun: true,
        }}
        config={{
          ...MOCK_CONFIG,
          targetingConfigs: [
            {
              label: "No Targeting",
              value: "",
              applicationValues: [
                NimbusExperimentApplicationEnum.DESKTOP,
                "TOASTER",
              ],
              description: "No Targeting configuration",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
              isFirstRunRequired: false,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
              isFirstRunRequired: false,
            },
            {
              label: "Mobile Only",
              value: "MOBILE_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.FENIX],
              description: "Mobile only configuration",
              stickyRequired: true,
              isFirstRunRequired: true,
            },
          ],
        }}
      />,
    );
    const targetingConfigSlug = (await screen.findByTestId(
      "targetingConfigSlug",
    )) as HTMLSelectElement;

    expect(targetingConfigSlug.value).toEqual(
      MOCK_CONFIG!.targetingConfigs![2]!.value,
    );
    fireEvent.change(screen.getByTestId("targetingConfigSlug"), {
      target: { value: MOCK_CONFIG!.targetingConfigs![0]!.value },
    });
    fireEvent.click(screen.getByTestId("isFirstRun"), {
      target: { checked: false },
    });
    expect(screen.getByTestId("isFirstRun")).toHaveProperty("checked", true);
    expect(screen.getByTestId("isFirstRun")).toBeDisabled();
    await expect(
      screen.queryByTestId("is-first-run-required-warning"),
    ).toBeInTheDocument();
  });

  it("expect First Run to be  unchecked", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isFirstRun: false,
        }}
      />,
    );

    expect(screen.getByTestId("isFirstRun")).not.toBeChecked();
  });

  it("expect First Run to be checked", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isFirstRun: true,
        }}
      />,
    );

    expect(screen.getByTestId("isFirstRun")).toBeChecked();
  });

  it("change First Run to be checked", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isFirstRun: false,
        }}
      />,
    );
    fireEvent.click(screen.getByTestId("isFirstRun"));
    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(screen.getByTestId("isFirstRun")).toBeChecked();
  });

  it("change First Run to be unchecked", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          channel: NimbusExperimentChannelEnum.NIGHTLY,
          isFirstRun: true,
        }}
      />,
    );
    fireEvent.click(screen.getByTestId("isFirstRun"));
    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(screen.getByTestId("isFirstRun")).not.toBeChecked();
  });

  it("renders server errors", async () => {
    const submitErrors = {
      "*": ["Big bad server thing happened"],
      channel: ["Cannot tune in this channel"],
      firefox_min_version: ["Bad min version"],
      firefox_max_version: ["Bad max version"],
      targeting_config_slug: ["This slug is icky"],
      countries: ["This place doesn't even exist"],
      locales: ["We don't have that locale"],
      population_percent: ["This is not a percentage"],
      total_enrolled_clients: ["Need a number here, bud."],
      proposed_enrollment: ["Emoji are not numbers"],
      proposed_duration: ["No negative numbers"],
    };
    render(<Subject submitErrors={submitErrors} />);
    await screen.findByTestId("FormAudience");
    for (const [submitErrorName, [error]] of Object.entries(submitErrors)) {
      const fieldName = snakeToCamelCase(submitErrorName);
      if (fieldName === "*") {
        expect(screen.getByTestId("submit-error")).toHaveTextContent(error);
      } else {
        await screen.findByText(error, {
          selector: `.invalid-feedback[data-for=${fieldName}]`,
        });
      }
    }
  });

  it("renders without error with default values", async () => {
    renderSubjectWithDefaultValues();
    await screen.findByTestId("FormAudience");

    for (const [fieldName, expected] of [
      ["firefoxMinVersion", NimbusExperimentFirefoxVersionEnum.NO_VERSION],
      ["firefoxMaxVersion", NimbusExperimentFirefoxVersionEnum.NO_VERSION],
      ["populationPercent", "0"],
      ["proposedDuration", "0"],
      ["proposedEnrollment", "0"],
      ["targetingConfigSlug", ""],
    ] as const) {
      const field = screen.queryByTestId(fieldName);
      expect(field).toBeInTheDocument();
      expect((field as HTMLInputElement).value).toEqual(expected);
    }

    expect(screen.getByTestId("locales")).toHaveTextContent("All Locales");
    expect(screen.getByTestId("countries")).toHaveTextContent("All Countries");
  });

  it("enables language field for mobile", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
        }}
      />,
    );

    expect(screen.queryByTestId("languages")).toBeInTheDocument();
    expect(screen.queryByTestId("locales")).not.toBeInTheDocument();
  });

  it.each(
    Object.values(NimbusExperimentApplicationEnum).filter((application) =>
      MOBILE_APPLICATIONS.includes(application),
    ),
  )("isFirstRun renders for mobile application", (application) => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application,
        }}
      />,
    );

    expect(screen.queryByTestId("isFirstRun")).toBeInTheDocument();
  });

  it.each(
    Object.values(NimbusExperimentApplicationEnum).filter(
      (application) => !MOBILE_APPLICATIONS.includes(application),
    ),
  )("isFirstRun does not render for non mobile application", (application) => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application,
        }}
      />,
    );

    expect(screen.queryByTestId("isFirstRun")).not.toBeInTheDocument();
  });

  it("disables language field for desktop", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
        }}
      />,
    );

    expect(screen.queryByTestId("languages")).not.toBeInTheDocument();
    expect(screen.queryByTestId("locales")).toBeInTheDocument();
  });

  it("calls onSubmit when save and next buttons are clicked", async () => {
    const onSubmit = jest.fn();
    const expected: ExperimentInput = {
      channel: MOCK_EXPERIMENT.channel,
      firefoxMinVersion: MOCK_EXPERIMENT.firefoxMinVersion,
      firefoxMaxVersion: MOCK_EXPERIMENT.firefoxMaxVersion,
      targetingConfigSlug: MOCK_EXPERIMENT.targetingConfigSlug,
      populationPercent: MOCK_EXPERIMENT.populationPercent,
      totalEnrolledClients: MOCK_EXPERIMENT.totalEnrolledClients,
      proposedEnrollment: "" + MOCK_EXPERIMENT.proposedEnrollment,
      proposedDuration: "" + MOCK_EXPERIMENT.proposedDuration,
      countries: MOCK_EXPERIMENT.countries.map((v) => "" + v.id),
      locales: MOCK_EXPERIMENT.locales.map((v) => "" + v.id),
      languages: MOCK_EXPERIMENT.languages.map((v) => "" + v.id),
      isSticky: MOCK_EXPERIMENT.isSticky,
      isFirstRun: MOCK_EXPERIMENT.isFirstRun,
      excludedExperimentsBranches: [
        {
          excludedExperiment: MOCK_EXPERIMENTS_BY_APPLICATION[0].id,
          branchSlug: null,
        },
      ],
      requiredExperimentsBranches: [
        {
          requiredExperiment: MOCK_EXPERIMENTS_BY_APPLICATION[1].id,
          branchSlug: null,
        },
      ],
    };
    const experiment: getExperiment_experimentBySlug = {
      ...MOCK_EXPERIMENT,
      excludedExperimentsBranches: [
        {
          excludedExperiment: MOCK_EXPERIMENTS_BY_APPLICATION[0],
          branchSlug: null,
        },
      ],
      requiredExperimentsBranches: [
        {
          requiredExperiment: MOCK_EXPERIMENTS_BY_APPLICATION[1],
          branchSlug: null,
        },
      ],
    };
    render(<Subject {...{ experiment, onSubmit }} />);
    await screen.findByTestId("FormAudience");
    const submitButton = screen.getByTestId("submit-button");
    const nextButton = screen.getByTestId("next-button");

    fireEvent.click(submitButton);
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(2);
      expect(onSubmit.mock.calls).toEqual([
        // Save button just saves
        [expected, false],
        // Next button advances to next page
        [expected, true],
      ]);
    });
  });

  it("accepts commas in the expected number of clients field (EXP-761)", async () => {
    const enteredValue = "123,456,789";
    const expectedValue = 123456789;

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = screen.getByTestId("totalEnrolledClients");
      fireEvent.change(field, { target: { value: enteredValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].totalEnrolledClients).toEqual(
      expectedValue,
    );
  });

  it("does not allow letters within the expected number of client field", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of ["totalEnrolledClients"]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.change(field, { target: { value: "1234abc" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
  });

  it("changing proposed release date sets form value", async () => {
    const enteredDate = "2023-05-12";

    const onSubmit = jest.fn();
    render(
      <Subject
        {...{ onSubmit }}
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          isFirstRun: true,
        }}
      />,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    const field = screen.getByTestId("proposedReleaseDate") as HTMLInputElement;
    fireEvent.change(field, { target: { value: enteredDate } });
    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].proposedReleaseDate).toEqual(enteredDate);
  });

  it("changing proposed release date to empty sets form value", async () => {
    const expectedDate = "";
    const onSubmit = jest.fn();

    render(
      <Subject
        {...{ onSubmit }}
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          isFirstRun: true,
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
      expect(screen.queryByTestId("proposedReleaseDate")).toBeInTheDocument();
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].proposedReleaseDate).toEqual(expectedDate);
  });

  it("only access proposed release date field for mobile applications", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          isFirstRun: true,
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("isFirstRun")).toBeInTheDocument();
      expect(screen.queryByTestId("proposedReleaseDate")).toBeInTheDocument();
    });
  });

  it("cannot access proposed release date field for desktop applications", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.queryByTestId("isFirstRun")).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("proposedReleaseDate"),
      ).not.toBeInTheDocument();
    });
  });

  it("clicking proposed release date title takes you to whattrainisit", async () => {
    const onSubmit = jest.fn();
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.FENIX,
          isFirstRun: true,
        }}
      />,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    const tooltipInfo = screen.getByTestId("tooltip-proposed-release-date");
    await act(async () => {
      fireEvent.click(tooltipInfo);
    });
    expect(mockWindowOpen).toBeCalledWith(EXTERNAL_URLS.WHAT_TRAIN_IS_IT);
  });

  it("using the population percent text box sets form value", async () => {
    const enteredValue = "45";
    const expectedValue = "45";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: enteredValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("population percent text box shows default value", async () => {
    const expectedValue = "0";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("using the population percent slider sets form value", async () => {
    const enteredValue = "45";
    const expectedValue = "45";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-slider");
      fireEvent.change(field, { target: { value: enteredValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("population percentage text input handles string number value", async () => {
    const stringValue = "45";
    const expectedValue = "45";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-slider");
      fireEvent.change(field, { target: { value: stringValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("population percentage text input handles decimals", async () => {
    const value = "45.1";
    const expectedValue = "45.1";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: value } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("population percentage text input handles null value", async () => {
    const initialValue = "45";
    const expectedValue = "45";

    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await screen.findByTestId("FormAudience");
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-slider");
      fireEvent.change(field, { target: { value: initialValue } });
      fireEvent.blur(field);
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);

    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: null } });
      fireEvent.blur(field);
    });

    await act(async () => {
      fireEvent.click(submitButton);
    });

    expect(onSubmit).toHaveBeenCalledTimes(2);
    expect(onSubmit.mock.calls[0][0].populationPercent).toEqual(expectedValue);
  });

  it("population percentage slider shows default when handling null value", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: null } });
    });

    const slider = within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-slider");

    expect((slider as HTMLInputElement).value).toEqual("50");
  });

  it("renders the pre-computed population sizing values", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.RELEASE,
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
            {
              name: "Canada",
              id: "2",
              code: "CA",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
            {
              name: "English (CA)",
              id: "2",
              code: "EN-CA",
            },
          ],
        }}
        config={{
          ...MOCK_CONFIG,
          applicationConfigs: [
            {
              application: NimbusExperimentApplicationEnum.DESKTOP,
              channels: [{ label: "Release", value: "RELEASE" }],
            },
          ],
          channels: [{ label: "Release", value: "RELEASE" }],
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
            {
              name: "Canada",
              id: "2",
              code: "CA",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
            {
              name: "English (CA)",
              id: "2",
              code: "EN-CA",
            },
          ],
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    expect(
      screen.getByText("Pre-computed population sizing data"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("10000 total", {
        exact: false,
      }),
    ).toBeInTheDocument();
    expect(screen.queryAllByText("Percent of clients:")).toHaveLength(12);
    expect(screen.queryAllByText("Expected number of clients:")).toHaveLength(
      12,
    );
  });

  it("renders the pre-computed population sizing values for mobile", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.IOS,
          channel: NimbusExperimentChannelEnum.RELEASE,
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
            {
              name: "Canada",
              id: "2",
              code: "CA",
            },
          ],
          languages: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
            {
              name: "English (CA)",
              id: "2",
              code: "EN-CA",
            },
          ],
        }}
        config={{
          ...MOCK_CONFIG,
          applicationConfigs: [
            {
              application: NimbusExperimentApplicationEnum.IOS,
              channels: [{ label: "Release", value: "RELEASE" }],
            },
          ],
          channels: [{ label: "Release", value: "RELEASE" }],
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
            {
              name: "Canada",
              id: "2",
              code: "CA",
            },
          ],
          languages: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
            {
              name: "English (CA)",
              id: "2",
              code: "EN-CA",
            },
          ],
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    expect(
      screen.getByText("Pre-computed population sizing data"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("10000 total", {
        exact: false,
      }),
    ).toBeInTheDocument();
    expect(screen.queryAllByText("Percent of clients:")).toHaveLength(12);
    expect(screen.queryAllByText("Expected number of clients:")).toHaveLength(
      12,
    );
  });

  it("does not render the pre-computed population sizing values when no match found", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.BETA,
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
          ],
        }}
        config={{
          ...MOCK_CONFIG,
          applicationConfigs: [
            {
              application: NimbusExperimentApplicationEnum.DESKTOP,
              channels: [
                { label: "Release", value: "RELEASE" },
                { label: "Beta", value: "BETA" },
              ],
            },
          ],
          channels: [
            { label: "Release", value: "RELEASE" },
            { label: "Beta", value: "BETA" },
          ],
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
          ],
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    expect(
      screen.queryByText("Pre-computed population sizing data"),
    ).not.toBeInTheDocument();
  });

  it("does not render the pre-computed population sizing values when no sizing data is available", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
          channel: NimbusExperimentChannelEnum.RELEASE,
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
          ],
        }}
        config={{
          ...MOCK_CONFIG,
          applicationConfigs: [
            {
              application: NimbusExperimentApplicationEnum.DESKTOP,
              channels: [{ label: "Release", value: "RELEASE" }],
            },
          ],
          channels: [{ label: "Release", value: "RELEASE" }],
          countries: [
            {
              name: "United States of America",
              id: "1",
              code: "US",
            },
          ],
          locales: [
            {
              name: "English (US)",
              id: "1",
              code: "EN-US",
            },
          ],
          populationSizingData: "{}",
        }}
      />,
    );
    await screen.findByTestId("FormAudience");
    expect(
      screen.queryByText("Pre-computed population sizing data"),
    ).not.toBeInTheDocument();
  });

  it("requires positive numbers in numeric fields (EXP-956)", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.change(field, { target: { value: "-123" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
  });

  it("does not have any required modified fields", async () => {
    const onSubmit = jest.fn();
    renderSubjectWithDefaultValues(onSubmit);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("submit-button"));
    });
    expect(onSubmit).toHaveBeenCalled();
  });

  it("does not call onSubmit when submitted while loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    const form = screen.getByTestId("FormAudience");
    await act(async () => {
      fireEvent.submit(form);
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("requires positive numbers in population percentage field", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: "-123" } });
    });
    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(
      within(screen.queryByTestId("population-percent-top-row") as HTMLElement)
        .findByText("This field", {
          selector: `.invalid-feedback[data-for={populationPercent}]`,
        })
        .then(() => {}),
    ).toBeTruthy();
  });

  it("requires numbers in population percentage field", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: "sdfds" } });
    });
    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });
    expect(
      within(screen.queryByTestId("population-percent-top-row") as HTMLElement)
        .findByText("This field", {
          selector: `.invalid-feedback[data-for={populationPercent}]`,
        })
        .then(() => {}),
    ).toBeTruthy();
  });

  it("allows the population percentage slider to be slid", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });
    await act(async () => {
      const slider = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-slider");
      fireEvent.change(slider, { target: { value: "100" } });
    });
    expect(
      within(screen.queryByTestId("population-percent-top-row") as HTMLElement)
        .findByText("100", {
          selector: `[data-for={populationPercent}]`,
        })
        .then(() => {}),
    ).toBeTruthy();
  });

  it("population percentage text input updates slider value", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    const expected = "50";
    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: expected } });
    });

    const slider = within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-slider");

    expect((slider as HTMLInputElement).value).toEqual(expected);
  });

  it("allows multiple changes to population percentage field", async () => {
    const onSubmit = jest.fn();
    const expectedValue = "75";

    const { container } = render(<Subject {...{ onSubmit }} />);

    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: "50" } });
    });

    expect(
      within(screen.queryByTestId("population-percent-top-row") as HTMLElement)
        .findByText("50", {
          selector: `[data-for={populationPercent}]`,
        })
        .then(() => {}),
    ).toBeTruthy();

    await act(async () => {
      const slider = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-slider");
      fireEvent.change(slider, { target: { value: "75" } });
    });

    expect(
      within(screen.queryByTestId("population-percent-top-row") as HTMLElement)
        .findByText(expectedValue, {
          selector: `[data-for={populationPercent}]`,
        })
        .then(() => {}),
    ).toBeTruthy();
  });

  it("displays expected message on number-based inputs when invalid", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.change(field, { target: { value: "hi" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
  });

  it("displays expected message on population percent when invalid", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);

    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    await act(async () => {
      const field = within(
        screen.queryByTestId("population-percent-top-row") as HTMLElement,
      ).getByTestId("population-percent-text");
      fireEvent.change(field, { target: { value: "6666666" } });
    });

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(
        within(
          screen.queryByTestId("population-percent-top-row") as HTMLElement,
        )
          .findByText("This field", {
            selector: `.invalid-feedback[data-for={populationPercent}]`,
          })
          .then(() => {}),
      ).toBeTruthy();
    });
  });

  it("can display server review-readiness messages on all fields", async () => {
    await assertSerializerMessages(Subject, {
      population_percent: ["When it feels like the world is on your shoulders"],
      proposed_duration: ["And all the madness has got you goin' crazy"],
      proposed_enrollment: ["It's time to get out"],
      total_enrolled_clients: ["Step out into the street"],
      firefox_min_version: [
        "Where all of the action is right there at your feet.",
      ],
      targeting_config_slug: [
        "Well, I know a place",
        "Where we can dance the whole night away",
      ],
      channel: ["Underneath the electric stars."],
      countries: ["Just come with me"],
      locales: ["We can shake it loose right away"],
    });
  });
});

it("fields should be enabled for draft experiments", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.FENIX,
        isRollout: false,
        status: NimbusExperimentStatusEnum.DRAFT,
        targetingConfig: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
      }}
    />,
  );
  expect(screen.getByTestId("isSticky")).toBeEnabled();
  expect(screen.getByTestId("firefoxMinVersion")).toBeEnabled();
  expect(screen.getByTestId("channel")).toBeEnabled();
});

it("enables fields and buttons for live rollouts", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_ROLLOUT,
        application: NimbusExperimentApplicationEnum.FENIX,
        isRollout: true,
        status: NimbusExperimentStatusEnum.LIVE,
        targetingConfig: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
      }}
    />,
  );
  expect(screen.getByTestId("submit-button")).toBeEnabled();
  expect(screen.getByTestId("next-button")).toBeEnabled();
  expect(
    within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-text"),
  ).toBeEnabled();
  expect(
    within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-slider"),
  ).toBeEnabled();
  expect(screen.getByTestId("isSticky")).toBeDisabled();
  expect(screen.getByTestId("firefoxMinVersion")).toBeDisabled();
  expect(screen.getByTestId("channel")).toBeDisabled();
});

it("enables fields when unlocked", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.FENIX,
        isRollout: false,
        status: NimbusExperimentStatusEnum.DRAFT,
        targetingConfig: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
      }}
    />,
  );
  expect(screen.getByTestId("submit-button")).toBeEnabled();
  expect(screen.getByTestId("next-button")).toBeEnabled();
  expect(
    within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-text"),
  ).toBeEnabled();
  expect(
    within(
      screen.queryByTestId("population-percent-top-row") as HTMLElement,
    ).getByTestId("population-percent-slider"),
  ).toBeEnabled();
  expect(screen.queryByTestId("isSticky")).toBeEnabled();
  expect(screen.queryByTestId("firefoxMinVersion")).toBeEnabled();
  expect(screen.queryByTestId("channel")).toBeEnabled();
});

it("disables save buttons when archived", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.FENIX,
        isRollout: false,
        status: NimbusExperimentStatusEnum.DRAFT,
        targetingConfig: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
        isArchived: true,
      }}
    />,
  );
  expect(screen.getByTestId("submit-button")).toBeDisabled();
  expect(screen.getByTestId("next-button")).toBeDisabled();
});

it("enables save buttons when not archived", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.FENIX,
        isRollout: false,
        status: NimbusExperimentStatusEnum.DRAFT,
        targetingConfig: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
        isArchived: false,
      }}
    />,
  );
  expect(screen.getByTestId("submit-button")).toBeEnabled();
  expect(screen.getByTestId("next-button")).toBeEnabled();
});

it("disable enrollment period when experiment is a rollout", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_ROLLOUT,
        application: NimbusExperimentApplicationEnum.DESKTOP,
        channel: NimbusExperimentChannelEnum.NIGHTLY,
        status: NimbusExperimentStatusEnum.DRAFT,
        isRollout: true,
        firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_107,
      }}
    />,
  );

  await waitFor(() => {
    expect(screen.queryByTestId("proposedEnrollment")).toBeDisabled();
    screen.getByTestId("tooltip-disabled");
  });
});

it("enrollment period is not diabled when experiment is not a rollout", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_ROLLOUT,
        application: NimbusExperimentApplicationEnum.DESKTOP,
        channel: NimbusExperimentChannelEnum.NIGHTLY,
        status: NimbusExperimentStatusEnum.DRAFT,
        isRollout: false,
        firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_107,
      }}
    />,
  );
  await waitFor(() => {
    expect(screen.getByTestId("proposedEnrollment")).not.toBeDisabled();
    expect(screen.queryByTestId("tooltip-disabled")).toBeNull();
  });
});

it("disable fields for web application", async () => {
  render(
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.MONITOR,
        channel: NimbusExperimentChannelEnum.STAGING,
        status: NimbusExperimentStatusEnum.DRAFT,
        isWeb: true,
        firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
        firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
        populationPercent: "0",
        proposedDuration: 0,
        proposedEnrollment: 0,
        proposedReleaseDate: "",
        countries: [],
        languages: [],
      }}
    />,
  );
  expect(screen.queryByTestId("firefoxMinVersion")).toBeDisabled();
  screen.getByTestId("tooltip-disabled-min-version");

  expect(screen.queryByTestId("firefoxMaxVersion")).toBeDisabled();
  screen.getByTestId("tooltip-disabled-max-version");

  const countriesDiv = document.querySelector('[data-testid="countries"]');
  const selectCountriesElement = countriesDiv?.querySelector("input");
  expect(selectCountriesElement).toHaveAttribute("disabled");

  const languagesDiv = document.querySelector('[data-testid="languages"]');
  const selectLanguagesElement = languagesDiv?.querySelector("input");
  expect(selectLanguagesElement).toHaveAttribute("disabled");

  expect(screen.queryByTestId("isSticky")).toBeDisabled();
  screen.getByTestId("tooltip-disabled-is-sticky");
});
describe("filterAndSortTargetingConfigSlug", () => {
  it("filters for experiment application and sorts them as expected", () => {
    const expectedNoTargetingLabel = "No Targeting";
    const expectedLabel = "Foo Bar";
    const expectedMissingLabel = "Baz Quux";
    const expectedLastLabel = "Zebra";
    const application = NimbusExperimentApplicationEnum.DESKTOP;
    const targetingConfigSlug = [
      {
        label: expectedNoTargetingLabel,
        value: "",
        applicationValues: [application, NimbusExperimentApplicationEnum.IOS],
        description: "",
        stickyRequired: false,
        isFirstRunRequired: false,
      },
      {
        label: expectedLastLabel,
        value: "ZEBRA",
        applicationValues: [application],
        description: "",
        stickyRequired: false,
        isFirstRunRequired: false,
      },
      {
        label: expectedLabel,
        value: "FOO_BAR",
        applicationValues: [application],
        description: "",
        stickyRequired: false,
        isFirstRunRequired: false,
      },
      {
        label: expectedMissingLabel,
        value: "BAZ_QUUX",
        applicationValues: [NimbusExperimentApplicationEnum.IOS],
        description: "",
        stickyRequired: false,
        isFirstRunRequired: false,
      },
    ];
    const result = filterAndSortTargetingConfigs(
      targetingConfigSlug,
      application,
    );
    expect(result).toHaveLength(3);
    expect(
      result.find((item) => item.label === expectedNoTargetingLabel),
    ).toBeDefined();
    expect(result.find((item) => item.label === expectedLabel)).toBeDefined();
    expect(
      result.find((item) => item.label === expectedMissingLabel),
    ).toBeUndefined();
    // check sorting (default value first, then alphabetical)
    expect(result[0].label).toEqual(expectedNoTargetingLabel);
    expect(result[result.length - 1].label).toEqual(expectedLastLabel);
  });
});

const renderSubjectWithDefaultValues = (onSubmit = () => {}) =>
  render(
    <Subject
      {...{ onSubmit }}
      config={{
        ...MOCK_CONFIG,
        targetingConfigs: [
          {
            label: "No Targeting",
            value: "",
            applicationValues: [
              NimbusExperimentApplicationEnum.DESKTOP,
              "TOASTER",
            ],
            description: "No targeting configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
          {
            label: "Mac Only",
            value: "MAC_ONLY",
            applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
            description: "Mac only configuration",
            stickyRequired: true,
            isFirstRunRequired: false,
          },
          {
            label: "Some toaster thing",
            value: "SOME_TOASTER_THING",
            applicationValues: ["TOASTER"],
            description: "Some toaster thing configuration",
            stickyRequired: false,
            isFirstRunRequired: false,
          },
        ],
        firefoxVersions: [
          {
            label: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
            value: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
          },
        ],
        channels: [
          {
            label: NimbusExperimentChannelEnum.NO_CHANNEL,
            value: NimbusExperimentChannelEnum.NO_CHANNEL,
          },
        ],
      }}
      experiment={{
        ...MOCK_EXPERIMENT,
        application: NimbusExperimentApplicationEnum.DESKTOP,
        firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
        firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum.NO_VERSION,
        channel: NimbusExperimentChannelEnum.NO_CHANNEL,
        populationPercent: "0",
        proposedDuration: 0,
        proposedEnrollment: 0,
        proposedReleaseDate: "",
        targetingConfigSlug: "",
        countries: [],
        locales: [],
        languages: [],
      }}
    />,
  );
