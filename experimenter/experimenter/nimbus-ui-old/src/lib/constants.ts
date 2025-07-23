/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RegisterOptions } from "react-hook-form";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

export const BASE_PATH = "/nimbus";

export const UNKNOWN_ERROR =
  "Sorry, an error occurred but we don't know why. We're looking into it.";
export const SUBMIT_ERROR =
  "Sorry, an error occurred while submitting. Please try again.";

export const CONTROL_BRANCH_REQUIRED_ERROR = "Control branch is required";

export const SAVE_FAILED_NO_ERROR = "Save failed, no error available";

export const SAVE_FAILED_QA_STATUS = "Failed to save qa status.";

export const CONFIG_EMPTY_ERROR = "Configuration is empty";

export const INVALID_CONFIG_ERROR = "Invalid configuration";

export const ARCHIVE_DISABLED =
  "Experiments can only be archived when in Draft or Complete.";

export const SERVER_ERRORS = {
  REQUIRED_QUESTION: "This question may not be blank.",
  NULL_FIELD: "This field may not be null.",
  EMPTY_LIST: "This list may not be empty.",
  BLANK_DESCRIPTION: "Description may not be blank.",
  FEATURE_CONFIGS:
    "You must select a feature configuration from the drop down.",
};

export const EXTERNAL_URLS = {
  TRAINING_AND_PLANNING_DOC: "https://experimenter.info/for-product",
  NIMBUS_MANA_DOC: "https://mana.mozilla.org/wiki/display/FJT/Nimbus",
  WORKFLOW_MANA_DOC:
    "https://experimenter.info/data-scientists/#sample-size-recommendations",
  BRANCHES_EXPERIMENTER_DOC: "https://experimenter.info/feature-definition/",
  METRICS_EXPERIMENTER_DOC:
    "https://experimenter.info/deep-dives/jetstream/metrics",
  // EXP-866 TBD URL
  PREVIEW_LAUNCH_DOC: "https://mana.mozilla.org/wiki/display/FJT/Nimbus",
  RISK_BRAND: "https://experimenter.info/comms-sign-off",
  RISK_MESSAGE:
    "https://mozilla-hub.atlassian.net/wiki/spaces/FIREFOX/pages/208308555/Message+Consult+Creation",
  RISK_PARTNER: "https://experimenter.info/legal-sign-off",
  RISK_REVENUE: "https://experimenter.info/vp-sign-off",
  SIGNOFF_QA: "https://experimenter.info/qa-sign-off",
  SIGNOFF_VP: "https://experimenter.info/vp-sign-off",
  SIGNOFF_LEGAL: "https://experimenter.info/legal-sign-off",
  REVIEW_PRIVILIGES: "https://experimenter.info/access",
  ROLLOUT_SETPREF_REENROLL_EXPLANATION:
    "https://experimenter.info/faq/warnings#rollouts-and-setpref-interaction-desktop",
  EXPERIMENTER_DOCUMENTATION: "https://experimenter.info",
  ASK_EXPERIMENTER_SLACK: "https://slack.com/app_redirect?channel=CF94YGE03",
  FEEDBACK: "https://bit.ly/38dgkqR",
  GITHUB_TICKET: "https://github.com/mozilla/experimenter/issues/new",
  DETAILED_ANALYSIS_TEMPLATE: (slug: string) =>
    `https://protosaur.dev/partybal/${slug.replace(/-/g, "_")}.html`,
  LAUNCH_DOCUMENTATION:
    "https://experimenter.info/access#onboarding-for-new-reviewers-l3",
  BUCKET_WARNING_EXPLANATION:
    "https://experimenter.info/faq/warnings#rollout-bucketing-warning",
  AUDIENCE_OVERLAP_WARNING:
    "https://experimenter.info/faq/warnings/#audience-overlap",
  CUSTOM_AUDIENCES_EXPLANATION:
    "https://experimenter.info/workflow/implementing/custom-audiences",
  WHAT_TRAIN_IS_IT: "https://whattrainisitnow.com",
  QA_PI_DOC:
    "https://mozilla-hub.atlassian.net/jira/software/c/projects/QA/boards/261",
};

export const RISK_QUESTIONS = {
  BRAND:
    "If the public, users or press, were to discover this experiment and description, do you think it could negatively impact their perception of the brand?",
  MESSAGE:
    "Does your experiment include ANY messages? If yes, this requires the",
  PARTNER:
    "Does this experiment rely on AI (e.g. ML, chatbot), impact or rely on a partner or outside company (e.g. Google, Amazon), or deliver any encryption or VPN?",
  REVENUE:
    "Does this experiment have a risk to negatively impact revenue (e.g. search, Pocket revenue)?",
};

export const TOOLTIP_DURATION =
  "This is the total duration of the experiment, including the enrollment period.";
export const TOOLTIP_DISABLED = "Enrollment Period is disabled on rollouts";
export const TOOLTIP_DISABLED_FOR_WEBAPP =
  "This field is not applicable for web based application";
export const TOOLTIP_RELEASE_DATE =
  "This is the approximate release date of the version that is being targeted. Click here to find your date!";

export const AUDIENCE_OVERLAP_WARNINGS = {
  EXCLUDING_EXPERIMENTS_WARNING: `The following experiments are being excluded by your experiment and may reduce the eligible population for your experiment which may result in reduced statistical power and precision. Please check that the configured population proportion has accounted for this: `,
  LIVE_EXPERIMENTS_BUCKET_WARNING: `The following experiments are LIVE on a previous namespace and may reduce the eligible population for your experiment which may result in reduced statistical power and precision. Please check that the configured population proportion has accounted for this: `,
  LIVE_MULTIFEATURE_WARNING: `The following multi-feature experiments are LIVE and may reduce the eligible population for your experiment which may result in reduced statistical power and precision. Please check that the configured population proportion has accounted for this: `,
};

export const LIFECYCLE_REVIEW_FLOWS = {
  LAUNCH: {
    buttonTitle: "Launch Experiment",
    description: "launch this experiment",
    requestSummary: "Requested Launch",
    reviewSummary: "Review Launch Request",
  },
  UPDATE: {
    buttonTitle: "Update Rollout",
    description: "update this rollout",
    requestSummary: "Requested Update",
    reviewSummary: "Review Update Request",
  },
  PAUSE: {
    buttonTitle: "End Enrollment for Experiment",
    description: "end enrollment for this experiment",
    requestSummary: "Requested End Enrollment",
    reviewSummary: "Review End Enrollment Request",
  },
  END: {
    buttonTitle: "End Experiment",
    description: "end this experiment",
    requestSummary: "Requested End",
    reviewSummary: "Review End Request",
  },
  NONE: {
    buttonTitle: "",
    description: "",
    requestSummary: "",
    reviewSummary: "",
  },
} as const;

export const CHANGELOG_MESSAGES = {
  CREATED_EXPERIMENT: "Created Experiment",
  UPDATED_BRANCHES: "Updated Branches",
  UPDATED_AUDIENCE: "Updated Audience",
  UPDATED_OUTCOMES: "Updated Outcomes",
  UPDATED_OVERVIEW: "Updated Overview",
  LAUNCHED_TO_PREVIEW: "Launched to Preview",
  RETURNED_TO_DRAFT: "Returned to Draft Status",
  RETURNED_TO_LIVE: "Returned to Live Dirty Status",
  REQUESTED_REVIEW: "Review Requested for Launch",
  REVIEW_APPROVED: "Launch Review Approved",
  REQUESTED_REVIEW_UPDATE: "Review Requested for Update",
  REVIEW_APPROVED_UPDATE: "Update Review Approved",
  REQUESTED_REVIEW_END_ENROLLMENT: "Requested Review to End Enrollment",
  END_ENROLLMENT_APPROVED: "End Enrollment Approved",
  REQUESTED_REVIEW_END: "Requested Review to End",
  END_APPROVED: "End Review Approved",
  ARCHIVING_EXPERIMENT: "Archiving experiment",
  UNARCHIVING_EXPERIMENT: "Unarchiving experiment",
  UPDATED_TAKEAWAYS: "Updated Takeaways",
  UPDATED_QA_STATUS: "Updated QA Status",
  UPDATE_SUBSCRIBERS: "Updated Subscribers",
  UPDATE_SIGNOFF: "Updated Signoffs",
  CANCEL_REVIEW: "Cancelled Review Request",
} as const;

export const FIELD_MESSAGES = {
  REQUIRED: "This field may not be blank.",
  NUMBER: "This field must be a number.",
  POSITIVE_NUMBER: "This field must be a positive number.",
  URL: "This field must be a URL.",
};

export const PUBLIC_DESCRIPTION_PLACEHOLDER =
  "The public description should be descriptive and publicly appropriate in order to avoid user confusion if they were to see it. It should avoid being too technical or too detailed.";

export const REQUIRED_FIELD = {
  required: FIELD_MESSAGES.REQUIRED,
} as RegisterOptions;

export const NUMBER_FIELD = {
  validate: (value) => (!!value && !isNaN(value)) || FIELD_MESSAGES.NUMBER,
} as RegisterOptions;

export const POSITIVE_NUMBER_FIELD = {
  validate: (value) =>
    (!!value && !isNaN(value) && value >= 0) || FIELD_MESSAGES.POSITIVE_NUMBER,
} as RegisterOptions;

export const POSITIVE_NUMBER_WITH_COMMAS_FIELD = {
  setValueAs: (value?: string) =>
    parseFloat(value?.trim().replace(/[^\d.-]+/g, "") ?? ""),

  validate: (value?: string) =>
    /^[0-9, ]*$/.test(value ?? "") || FIELD_MESSAGES.POSITIVE_NUMBER,
} as RegisterOptions;

export const URL_FIELD = {
  pattern: {
    value: /^(http|https):\/\/[^ "]+$/,
    message: FIELD_MESSAGES.URL,
  },
} as RegisterOptions;

export const IMAGE_UPLOAD_ACCEPT = ".gif,.jpg,.jpeg,.png";

export const START_POLL_INTERVAL = 30000; // 30 seconds
export const MAX_POLL_INTERVAL = 3600000; // 1 hour

interface QAStatusProperties {
  emoji: string;
  description: string;
  className: string;
}

export const QA_STATUS_PROPERTIES: Record<
  NimbusExperimentQAStatusEnum,
  QAStatusProperties
> = {
  [NimbusExperimentQAStatusEnum.GREEN]: {
    emoji: "✅",
    description: "✅ QA: Green",
    className: "success",
  },
  [NimbusExperimentQAStatusEnum.YELLOW]: {
    emoji: "⚠️",
    description: "⚠️ QA: Yellow",
    className: "text-dark",
  },
  [NimbusExperimentQAStatusEnum.RED]: {
    emoji: "❌",
    description: "❌ QA: Red",
    className: "danger",
  },
  [NimbusExperimentQAStatusEnum.SELF_GREEN]: {
    emoji: "✅",
    description: "✅ Self QA: Green",
    className: "success",
  },
  [NimbusExperimentQAStatusEnum.SELF_YELLOW]: {
    emoji: "⚠️",
    description: "⚠️ Self QA: Yellow",
    className: "text-dark",
  },
  [NimbusExperimentQAStatusEnum.SELF_RED]: {
    emoji: "❌",
    description: "❌ Self QA: Red",
    className: "danger",
  },
  [NimbusExperimentQAStatusEnum.NOT_SET]: {
    emoji: "⌛️",
    description: "⌛️ QA: Not set",
    className: "",
  },
};
