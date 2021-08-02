/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import ConfidenceInterval from ".";
import { SIGNIFICANCE } from "../../../lib/visualization/constants";

const Subject = ({
  ...props
}: React.ComponentProps<typeof ConfidenceInterval>) => (
  <ConfidenceInterval {...props} />
);

export default {
  title: "pages/Results/ConfidenceInterval",
  component: Subject,
  decorators: [
    withLinks,
    (story: () => React.ReactNode) => (
      <div className="w-25">
        <div className="w-75">{story()}</div>
      </div>
    ),
  ],
};

const storyWithProps = (
  props: React.ComponentProps<typeof Subject>,
  storyName?: string,
) => {
  const story = () => <Subject {...props} />;
  if (storyName) story.storyName = storyName;
  return story;
};

export const WithPositiveSignificance = storyWithProps({
  upper: 65,
  lower: 25,
  range: 65,
  significance: SIGNIFICANCE.POSITIVE,
});

export const WithNeutralSignificance = storyWithProps({
  upper: 65,
  lower: -45,
  range: 65,
  significance: SIGNIFICANCE.NEUTRAL,
});

export const WithNegativeSignificance = storyWithProps({
  upper: 65,
  lower: -45,
  range: 65,
  significance: SIGNIFICANCE.NEGATIVE,
});

export const WithSmallPositiveSignificance = storyWithProps({
  upper: 50,
  lower: 45,
  range: 50,
  significance: SIGNIFICANCE.POSITIVE,
});

export const WithSmallNeturalSignificance = storyWithProps({
  upper: 50,
  lower: 45,
  range: 50,
  significance: SIGNIFICANCE.NEUTRAL,
});

export const With3DigitBounds = storyWithProps({
  upper: 15,
  lower: 9,
  range: 20,
  significance: SIGNIFICANCE.POSITIVE,
});

export const With4DigitBoundsAndSmallNegativeSignificance = storyWithProps({
  upper: -8,
  lower: -11.8,
  range: 80,
  significance: SIGNIFICANCE.NEGATIVE,
});

export const With4DigitBoundsAndPositiveSignificance = storyWithProps({
  upper: 123,
  lower: 90,
  range: 123,
  significance: SIGNIFICANCE.POSITIVE,
});

export const With5DigitBoundsAndSmallNeutralSignificance = storyWithProps({
  upper: -10.9,
  lower: -15.1,
  range: 15.1,
  significance: SIGNIFICANCE.NEUTRAL,
});

export const With6DigitBoundsAndSmallPositiveSignificance = storyWithProps({
  upper: 123,
  lower: 90.5,
  range: 123,
  significance: SIGNIFICANCE.POSITIVE,
});

export const With8DigitBoundsAndPositiveSignificance = storyWithProps({
  upper: 1000,
  lower: 500.5,
  range: 1200,
  significance: SIGNIFICANCE.POSITIVE,
});

export const With10DigitBoundsAndSmallPositiveSignificance = storyWithProps({
  upper: 1234.5,
  lower: 1100.5,
  range: 1234.5,
  significance: SIGNIFICANCE.POSITIVE,
});

export const With10DigitBoundsAndLargeNegativeSignificance = storyWithProps({
  upper: -1000.5,
  lower: -7000,
  range: 7000,
  significance: SIGNIFICANCE.NEGATIVE,
});

export const With12DigitBounds = storyWithProps({
  upper: 64858.6,
  lower: 11854.4,
  range: 64858.6,
  significance: SIGNIFICANCE.POSITIVE,
});
