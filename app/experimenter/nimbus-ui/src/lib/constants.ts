/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RegisterOptions } from "react-hook-form";

export const BASE_PATH = "/nimbus";

export const UNKNOWN_ERROR =
  "Sorry, an error occurred but we don't know why. We're looking into it.";
export const SUBMIT_ERROR =
  "Sorry, an error occurred while submitting. Please try again.";

export const EXTERNAL_URLS = {
  RISK_MITIGATION_TEMPLATE_DOC:
    "https://docs.google.com/document/d/1zfG2g6pYe9aB7ItViQaw8OcOsXXdRUP70zpZoNC2xcA/edit",
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
};

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
