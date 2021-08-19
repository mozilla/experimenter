/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import TooltipWithMarkdown from ".";
import { ReactComponent as Info } from "../../../images/info.svg";
import { MOCK_METADATA } from "../../../lib/visualization/mocks";

const Subject = ({ id, description }: { id: string; description: string }) => (
  <div className="p-5">
    <Info data-tip data-for={id} />
    <TooltipWithMarkdown tooltipId={id} markdown={description} />
  </div>
);

export default {
  title: "components/TooltipWithMarkdown",
  component: Subject,
};

const storyWithProps = (
  props: React.ComponentProps<typeof Subject>,
  storyName?: string,
) => {
  const story = () => <Subject {...props} />;
  if (storyName) story.storyName = storyName;
  return story;
};

export const WithStringAndMarkdownLink = storyWithProps({
  id: MOCK_METADATA.metrics.feature_b.friendly_name,
  description: MOCK_METADATA.metrics.feature_b.description,
});

export const WithIndentation = storyWithProps({
  id: MOCK_METADATA.metrics.feature_b.friendly_name,
  description: "        This gets wrapped in <pre> and <code>.",
});
