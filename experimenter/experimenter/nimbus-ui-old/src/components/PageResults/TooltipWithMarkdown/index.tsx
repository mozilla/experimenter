/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ReactMarkdown from "react-markdown";
import ReactTooltip from "react-tooltip";

type TooltipWithMarkdownProps = {
  tooltipId: string;
  markdown: string;
};

const TooltipWithMarkdown = ({
  tooltipId,
  markdown,
}: TooltipWithMarkdownProps) => {
  return (
    <ReactTooltip
      id={tooltipId}
      multiline
      clickable
      className="w-25 font-weight-normal"
      delayHide={200}
      effect="solid"
    >
      <ReactMarkdown>{markdown!}</ReactMarkdown>
    </ReactTooltip>
  );
};

export default TooltipWithMarkdown;
