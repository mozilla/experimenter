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
  TRAINING_AND_PLANNING_DOC:
    "https://mana.mozilla.org/wiki/display/FJT/Nimbus+Onboarding",
  NIMBUS_MANA_DOC: "https://mana.mozilla.org/wiki/display/FJT/Nimbus",
  WORKFLOW_MANA_DOC:
    "https://experimenter.info/data-scientists/#sample-size-recommendations",
  BRANCHES_GOOGLE_DOC:
    "https://docs.google.com/document/d/155EUgzn22VTX8mFwesSROT3Z6JORSfb5VyoMoLra7ws/edit#heading=h.i8g4ppfvkq0x",
  METRICS_GOOGLE_DOC:
    "https://docs.google.com/document/d/155EUgzn22VTX8mFwesSROT3Z6JORSfb5VyoMoLra7ws/edit#heading=h.uq23fsvh16rc",
  // EXP-866 TBD URL
  PREVIEW_LAUNCH_DOC: "https://mana.mozilla.org/wiki/display/FJT/Nimbus",
  RISK_BRAND:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-Doesthishavehighrisktothebrand?",
  RISK_PARTNER:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-Isthisstudypartnerrelated?riskPARTNER",
  RISK_REVENUE:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-riskREV",
  SIGNOFF_QA:
    "https://docs.google.com/document/d/1oz1YyaaBI-oHUDsktWA-dLtX7WzhYqs7C121yOPKo2w/edit",
  SIGNOFF_VP:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-VPSign-offsignVP",
  SIGNOFF_LEGAL:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-signLEGAL",
  EXPERIMENTER_REVIEWERS:
    "https://mana.mozilla.org/wiki/display/FJT/Nimbus+Reviewers",
  EXPERIMENTER_DOCUMENTATION: "https://experimenter.info",
  ASK_EXPERIMENTER_SLACK: "https://slack.com/app_redirect?channel=CF94YGE03",
  FEEDBACK: "https://bit.ly/38dgkqR",
  GITHUB_TICKET: "https://github.com/mozilla/experimenter/issues/new",
  DETAILED_ANALYSIS_TEMPLATE: (slug: string) =>
    `https://protosaur.dev/partybal/${slug.replace(/-/g, "_")}.html`,
  LAUNCH_DOCUMENTATION:
    "https://experimenter.info/access#onboarding-for-new-reviewers-l3",
  BUCKET_WARNING_EXPLANATION:
    "https://experimenter.info/rollouts/rollouts-bucketing-warning",
  CUSTOM_AUDIENCES_EXPLANATION:
    "https://experimenter.info/workflow/implementing/custom-audiences",
  WHAT_TRAIN_IS_IT: "https://whattrainisitnow.com",
};

export const RISK_QUESTIONS = {
  BRAND:
    "If the public, users or press, were to discover this experiment and description, do you think it would negatively impact their perception of the brand?",
  PARTNER:
    "Does this experiment impact or rely on a partner or outside company (e.g. Google, Amazon)?",
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

export const POLL_INTERVAL = 30000;

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
  [NimbusExperimentQAStatusEnum.NOT_SET]: {
    emoji: "",
    description: "Not set",
    className: "",
  },
};
