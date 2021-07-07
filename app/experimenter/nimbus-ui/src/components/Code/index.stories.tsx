/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Code } from ".";

export default {
  title: "components/Code",
  component: Code,
  decorators: [
    (story: () => React.ReactNode) => <div className="p-5">{story()}</div>,
  ],
};

const storyWithChildren = (codeString: string, storyName?: string) => {
  const story = () => <Code {...{ codeString }} />;
  if (storyName) story.storyName = storyName;
  return story;
};

export const ShortJSONString = storyWithChildren(
  '{"list-discover-part": "red-firm-represent"}',
  "Short JSON string",
);

export const LongJSONString = storyWithChildren(
  '{ "id": "msw_skipFocus", "template": "multistage", "skipFocus": true, "screens": [ {"id": "AW_SET_DEFAULT", "order": 0, "content": { "zap": true, "title": { "string_id": "onboarding-multistage-set-default-header" }, "subtitle": { "string_id": "onboarding-multistage-set-default-subtitle" }, "primary_button": { "label": { "string_id": "onboarding-multistage-set-default-primary-button-label" }, "action": { "navigate": true, "type": "SET_DEFAULT_BROWSER" }}, "secondary_button": { "label": { "string_id": "onboarding-multistage-set-default-secondary-button-label" }, "action": { "navigate": true }}, "secondary_button_top": { "text": { "string_id": "onboarding-multistage-welcome-secondary-button-text" }, "label": { "string_id": "onboarding-multistage-welcome-secondary-button-label" }, "action": { "data": { "entrypoint": "activity-stream-firstrun" }, "type": "SHOW_FIREFOX_ACCOUNTS", "addFlowParams": true }}}}, { "id": "AW_IMPORT_SETTINGS", "order": 1, "content": { "zap": true, "disclaimer": { "string_id": "onboarding-import-sites-disclaimer" }, "title": { "string_id": "onboarding-multistage-import-header" }, "subtitle": { "string_id": "onboarding-multistage-import-subtitle" }, "tiles": { "type": "topsites", "showTitles": true }, "primary_button": { "label": { "string_id": "onboarding-multistage-import-primary-button-label" }, "action": { "type": "SHOW_MIGRATION_WIZARD", "navigate": true } }, "secondary_button": { "label": { "string_id": "onboarding-multistage-import-secondary-button-label" }, "action": { "navigate": true } } } }, { "id": "AW_CHOOSE_THEME", "order": 2, "content": { "zap": true, "title": { "string_id": "onboarding-multistage-theme-header" }, "subtitle": { "string_id": "onboarding-multistage-theme-subtitle" }, "tiles": { "type": "theme", "action": { "theme": "<event>" }, "data": [{ "theme": "automatic", "label": { "string_id": "onboarding-multistage-theme-label-automatic" }, "tooltip": { "string_id": "onboarding-multistage-theme-tooltip-automatic-2" }, "description": { "string_id": "onboarding-multistage-theme-description-automatic-2" } }, { "theme": "light", "label": { "string_id": "onboarding-multistage-theme-label-light" }, "tooltip": { "string_id": "onboarding-multistage-theme-tooltip-light-2" }, "description": { "string_id": "onboarding-multistage-theme-description-light" } }, { "theme": "dark", "label": { "string_id": "onboarding-multistage-theme-label-dark" }, "tooltip": { "string_id": "onboarding-multistage-theme-tooltip-dark-2" }, "description": { "string_id": "onboarding-multistage-theme-description-dark" } }, { "theme": "alpenglow", "label": { "string_id": "onboarding-multistage-theme-label-alpenglow" }, "tooltip": { "string_id": "onboarding-multistage-theme-tooltip-alpenglow-2" }, "description": { "string_id": "onboarding-multistage-theme-description-alpenglow" } } ] }, "primary_button": { "label": { "string_id": "onboarding-multistage-theme-primary-button-label" }, "action": { "navigate": true } }, "secondary_button": { "label": { "string_id": "onboarding-multistage-theme-secondary-button-label" }, "action": { "theme": "automatic", "navigate": true } } } } ] }',
  "Long JSON string",
);

export const NotJSON = storyWithChildren(
  "localeLanguageCode == 'en' && region == 'US'",
  "Not JSON (targeting expression)",
);
