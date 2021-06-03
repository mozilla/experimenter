/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RegisterOptions } from "react-hook-form";

export const BASE_PATH = "/nimbus";

export const UNKNOWN_ERROR =
  "Sorry, an error occurred but we don't know why. We're looking into it.";
export const SUBMIT_ERROR =
  "Sorry, an error occurred while submitting. Please try again.";

export const SERVER_ERRORS = {
  REQUIRED_QUESTION: "This question may not be blank.",
  NULL_FIELD: "This field may not be null.",
  EMPTY_LIST: "This list may not be empty.",
  BLANK_DESCRIPTION: "Description may not be blank.",
  FEATURE_CONFIG: "You must select a feature configuration from the drop down.",
};

export const EXTERNAL_URLS = {
  TRAINING_AND_PLANNING_DOC:
    "https://mana.mozilla.org/wiki/display/FJT/Nimbus+Onboarding",
  NIMBUS_MANA_DOC: "https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus",
  WORKFLOW_MANA_DOC:
    "https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=109990007",
  BRANCHES_GOOGLE_DOC:
    "https://docs.google.com/document/d/155EUgzn22VTX8mFwesSROT3Z6JORSfb5VyoMoLra7ws/edit#heading=h.i8g4ppfvkq0x",
  METRICS_GOOGLE_DOC:
    "https://docs.google.com/document/d/155EUgzn22VTX8mFwesSROT3Z6JORSfb5VyoMoLra7ws/edit#heading=h.uq23fsvh16rc",
  // EXP-866 TBD URL
  PREVIEW_LAUNCH_DOC:
    "https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus",
  RISK_BRAND:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-Doesthishavehighrisktothebrand?",
  RISK_PARTNER:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-Isthisstudypartnerrelated?riskPARTNER",
  RISK_REVENUE:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-riskREV",
  SIGNOFF_QA:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-QAsign-offsignQA",
  SIGNOFF_VP:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-VPSign-offsignVP",
  SIGNOFF_LEGAL:
    "https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#PrefFlipandAddOnExperiments-signLEGAL",
};

export const RISK_QUESTIONS = {
  BRAND:
    "If the public, users or press, were to discover this experiment and description, do you think it would negatively impact their perception of the brand?",
  PARTNER:
    "Does this experiment impact or rely on a partner or outside company (e.g. Google, Amazon)?",
  REVENUE:
    "Does this experiment have a risk to negatively impact revenue (e.g. search, Pocket revenue)?",
};

export const CHANGELOG_MESSAGES = {
  CREATED_EXPERIMENT: "Created Experiment",
  UPDATED_BRANCHES: "Updated Branches",
  UPDATED_AUDIENCE: "Updated Audience",
  UPDATED_OUTCOMES: "Updated Outcomes",
  UPDATED_OVERVIEW: "Updated Overview",
  LAUNCHED_TO_PREVIEW: "Launched to Preview",
  RETURNED_TO_DRAFT: "Returned to Draft Status",
  REQUESTED_REVIEW: "Review Requested for Launch",
  REVIEW_APPROVED: "Launch Review Approved",
  REQUESTED_REVIEW_END: "Requested Review to End",
  END_APPROVED: "End Review Approved",
} as const;

export const FIELD_MESSAGES = {
  REQUIRED: "This field may not be blank.",
  NUMBER: "This field must be a number.",
  POSITIVE_NUMBER: "This field must be a positive number.",
  URL: "This field must be a URL.",
};

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
  setValueAs: (value) =>
    parseFloat(("" + value).trim().replace(/[^\d.-]+/g, "")),
  validate: (value) =>
    (!isNaN(value) && value >= 0) || FIELD_MESSAGES.POSITIVE_NUMBER,
} as RegisterOptions;

export const URL_FIELD = {
  pattern: {
    value: /^(http|https):\/\/[^ "]+$/,
    message: FIELD_MESSAGES.URL,
  },
} as RegisterOptions;
