/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useContext } from "react";
import { ReactComponent as Info } from "../../../images/info.svg";
import { ResultsContext } from "../../../lib/contexts";
import {
  METRIC_TYPE,
} from "../../../lib/visualization/constants";
import TooltipWithMarkdown from "../TooltipWithMarkdown";


type MetricTypes =
  | typeof METRIC_TYPE.PRIMARY
  | typeof METRIC_TYPE.USER_SELECTED_SECONDARY
  | typeof METRIC_TYPE.DEFAULT_SECONDARY
  | typeof METRIC_TYPE.GUARDRAIL;

type MetricHeaderProps = {
  outcomeSlug: string;
  outcomeDefaultName: string;
  metricType?: MetricTypes;
};

const MetricHeader = ({
  outcomeSlug,
  outcomeDefaultName,
  metricType = METRIC_TYPE.DEFAULT_SECONDARY,
}: MetricHeaderProps) => {
  const {
    analysis: { metadata }
  } = useContext(ResultsContext);

  const outcomeName =
    metadata?.metrics[outcomeSlug]?.friendly_name || outcomeDefaultName;
  const outcomeDescription =
    metadata?.metrics[outcomeSlug]?.description || undefined;

  return (
    <h3 className="h5 mb-3" id={outcomeSlug}>
      <span className="mr-2">
        <span style={{ textTransform: 'capitalize' }}>{outcomeName}{" "}</span>
        {outcomeDescription && (
          <>
            <span className="align-middle">
              <Info
                className="align-baseline"
                data-tip
                data-for={outcomeSlug}
              />
            </span>
            <TooltipWithMarkdown
              tooltipId={outcomeSlug}
              markdown={outcomeDescription}
            />
          </>
        )}
      </span>
      <span
        className={`badge ${metricType.badge}`}
        data-tip={metricType.tooltip}
      >
        {metricType.label}
      </span>
    </h3>
  );
};

export default MetricHeader;
