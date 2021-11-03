/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import React from "react";
import Takeaways from ".";
import { NimbusExperimentConclusionRecommendation } from "../../../types/globalTypes";
import { Subject as BaseSubject, TAKEAWAYS_SUMMARY_LONG } from "./mocks";

export default {
  title: "pages/Results/Takeaways",
  component: Takeaways,
};

const submitAction = action("submit");

const Subject = ({
  onSubmit = async (data) => submitAction(data),
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject {...{ onSubmit, ...props }} />
);

export const Blank = () => <Subject />;

const commonContent = {
  takeawaysSummary: TAKEAWAYS_SUMMARY_LONG,
  conclusionRecommendation:
    NimbusExperimentConclusionRecommendation.CHANGE_COURSE,
};

export const WithContent = () => <Subject {...commonContent} />;

export const Editor = () => (
  <Subject {...{ ...commonContent, showEditor: true }} />
);

export const EditorIsLoading = () => (
  <Subject {...{ ...commonContent, showEditor: true, isLoading: true }} />
);

export const WithSubmitErrors = () => (
  <Subject
    {...{
      ...commonContent,
      showEditor: true,
      isServerValid: false,
      submitErrors: {
        "*": ["Meteor fell on the server!"],
        takeaways_summary: ["Too many mentions of chickens!"],
        conclusion_recommendation: ["'Ship it' is an invalid recommendation."],
      },
    }}
  />
);
