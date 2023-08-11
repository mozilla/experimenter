/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import React, { useState } from "react";
import Takeaways from "src/components/PageSummary/Takeaways";
import { RouterSlugProvider } from "src/lib/test-utils";

export const Subject = ({
  id = 123,
  takeawaysSummary = null,
  takeawaysQbrLearning = false,
  takeawaysMetricGain = false,
  takeawaysGainAmount = null,
  conclusionRecommendation = null,
  isLoading = false,
  isArchived = false,
  onSubmit = async (data) => {},
  ...props
}: Partial<React.ComponentProps<typeof Takeaways>>) => {
  const [showEditor, setShowEditor] = useState(
    typeof props.showEditor !== "undefined" ? props.showEditor : false,
  );
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>(
    props.submitErrors || {},
  );
  const isServerValid =
    typeof props.isServerValid !== "undefined" ? props.isServerValid : false;

  return (
    <RouterSlugProvider>
      <div className="p-4">
        <Takeaways
          {...{
            id,
            takeawaysSummary,
            takeawaysQbrLearning,
            takeawaysMetricGain,
            takeawaysGainAmount,
            conclusionRecommendation,
            isLoading,
            isArchived,
            onSubmit,
            showEditor,
            setShowEditor,
            submitErrors,
            setSubmitErrors,
            isServerValid,
            ...props,
          }}
        />
      </div>
    </RouterSlugProvider>
  );
};

export const TAKEAWAYS_SUMMARY_LONG = `
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec gravida est
quis libero convallis, nec dictum urna semper. Pellentesque lacinia orci eget
mi porta finibus. Phasellus gravida dui vel tellus interdum euismod. Nam
molestie, arcu vitae efficitur ullamcorper, velit orci ultrices turpis, eget
ullamcorper lacus risus nec mi. Nulla consectetur, urna quis efficitur
imperdiet, eros mauris lacinia ligula, mollis vestibulum enim massa vel nisl.
Donec nisi lorem, posuere sit amet mauris sed, pellentesque accumsan tortor.
Nam sollicitudin vitae justo posuere elementum. Nullam aliquet ante sed ante
dignissim porttitor. Fusce a pharetra mauris, nec facilisis urna. Fusce
scelerisque nisl sed venenatis imperdiet.

Vestibulum interdum suscipit eros a sodales. In suscipit turpis turpis. In
volutpat molestie odio sit amet imperdiet. Morbi et risus sed magna venenatis
pretium. Vestibulum congue, enim non faucibus tempor, lacus nulla blandit
nulla, eu ultricies mauris libero vel eros. Vestibulum mollis aliquam nulla,
at laoreet leo consectetur sed. Vestibulum ante ipsum primis in faucibus orci
luctus et ultrices posuere cubilia curae; Donec mattis ipsum a elit accumsan
mollis. Pellentesque a congue orci, vitae consequat lorem. Aenean vel auctor
lorem, ut aliquet est. Morbi venenatis justo consequat mollis blandit. Donec
cursus tempor rutrum. Sed sem massa, congue sed purus ac, vehicula hendrerit
ex. Interdum et malesuada fames ac ante ipsum primis in faucibus. Etiam
sagittis nec enim vitae rutrum.

Pellentesque non urna metus. Phasellus ligula felis, laoreet sit amet nisi
vitae, tempor ultricies metus. In metus odio, tincidunt sit amet eros ut,
vehicula elementum dolor. Pellentesque quis mollis nulla. In efficitur a leo
eu commodo. Maecenas finibus lectus et justo consequat condimentum. Morbi eu
tellus porta nisi egestas tempor condimentum eget urna.
`.trim();
