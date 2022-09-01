/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import { filterAndSortTargetingConfigs } from ".";
import { snakeToCamelCase } from "../../../lib/caseConversions";
import {
  EXTERNAL_URLS,
  FIELD_MESSAGES,
  TOOLTIP_DURATION,
} from "../../../lib/constants";
import { MOCK_CONFIG } from "../../../lib/mocks";
import { assertSerializerMessages } from "../../../lib/test-utils";
import {
  NimbusExperimentApplicationEnum,
  NimbusExperimentChannelEnum,
  NimbusExperimentFirefoxVersionEnum,
} from "../../../types/globalTypes";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

describe("FormAudience", () => {
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
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
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
    expect(screen.getByTestId("isFirstRun")).toBeChecked();
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
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
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
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
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
            },
            {
              label: "Win Only",
              value: "WIN_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Win Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
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
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId("isSticky")).toBeChecked();
    for (const fieldName of [
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
        fireEvent.change(field, { target: { value: "123" } });
        fireEvent.blur(field);
      });
      expect(screen.getByTestId("isSticky")).toBeChecked();
    }
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
            },
            {
              label: "Mac Only",
              value: "MAC_ONLY",
              applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
              description: "Mac Only configuration",
              stickyRequired: true,
            },
            {
              label: "Toaster thing",
              value: "TOASTER_THING",
              applicationValues: ["TOASTER"],
              description: "Toaster thing description",
              stickyRequired: false,
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

  it("expect First Run to be  unchecked", async () => {
    render(
      <Subject
        experiment={{
          ...MOCK_EXPERIMENT,
          application: NimbusExperimentApplicationEnum.DESKTOP,
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
          application: NimbusExperimentApplicationEnum.DESKTOP,
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
          application: NimbusExperimentApplicationEnum.DESKTOP,
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
          application: NimbusExperimentApplicationEnum.DESKTOP,
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
      ["populationPercent", "0.0"],
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
    const expected = {
      channel: MOCK_EXPERIMENT.channel,
      firefoxMinVersion: MOCK_EXPERIMENT.firefoxMinVersion,
      firefoxMaxVersion: MOCK_EXPERIMENT.firefoxMaxVersion,
      targetingConfigSlug: MOCK_EXPERIMENT.targetingConfigSlug,
      populationPercent: "" + MOCK_EXPERIMENT.populationPercent,
      totalEnrolledClients: MOCK_EXPERIMENT.totalEnrolledClients,
      proposedEnrollment: "" + MOCK_EXPERIMENT.proposedEnrollment,
      proposedDuration: "" + MOCK_EXPERIMENT.proposedDuration,
      countries: MOCK_EXPERIMENT.countries.map((v) => "" + v.id),
      locales: MOCK_EXPERIMENT.locales.map((v) => "" + v.id),
      languages: MOCK_EXPERIMENT.languages.map((v) => "" + v.id),
      isSticky: MOCK_EXPERIMENT.isSticky,
      isFirstRun: MOCK_EXPERIMENT.isFirstRun,
    };
    render(<Subject {...{ onSubmit }} />);
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
      fireEvent.click(field);
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

  it("requires positive numbers in numeric fields (EXP-956)", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
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

  it("displays expected message on number-based inputs when invalid", async () => {
    const onSubmit = jest.fn();
    const { container } = render(<Subject {...{ onSubmit }} />);
    await waitFor(() => {
      expect(screen.queryByTestId("FormAudience")).toBeInTheDocument();
    });

    for (const fieldName of [
      "populationPercent",
      "totalEnrolledClients",
      "proposedEnrollment",
      "proposedDuration",
    ]) {
      await act(async () => {
        const field = screen.getByTestId(fieldName);
        fireEvent.click(field);
        fireEvent.change(field, { target: { value: "hi" } });
        fireEvent.blur(field);
      });

      expect(
        container.querySelector(`.invalid-feedback[data-for=${fieldName}]`),
      ).toHaveTextContent(FIELD_MESSAGES.POSITIVE_NUMBER);
    }
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
      },
      {
        label: expectedLastLabel,
        value: "ZEBRA",
        applicationValues: [application],
        description: "",
        stickyRequired: false,
      },
      {
        label: expectedLabel,
        value: "FOO_BAR",
        applicationValues: [application],
        description: "",
        stickyRequired: false,
      },
      {
        label: expectedMissingLabel,
        value: "BAZ_QUUX",
        applicationValues: [NimbusExperimentApplicationEnum.IOS],
        description: "",
        stickyRequired: false,
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
          },
          {
            label: "Mac Only",
            value: "MAC_ONLY",
            applicationValues: [NimbusExperimentApplicationEnum.DESKTOP],
            description: "Mac only configuration",
            stickyRequired: true,
          },
          {
            label: "Some toaster thing",
            value: "SOME_TOASTER_THING",
            applicationValues: ["TOASTER"],
            description: "Some toaster thing configuration",
            stickyRequired: false,
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
        populationPercent: "0.0",
        proposedDuration: 0,
        proposedEnrollment: 0,
        targetingConfigSlug: "",
        countries: [],
        locales: [],
        languages: [],
      }}
    />,
  );
