import React from "react";
import ReactTooltip from "react-tooltip";

import {
  SIGNIFICANCE,
  METRIC,
} from "experimenter-rapid/components/visualization/constants/analysis";
import { SIGNIFICANCE_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";

const showSignificanceField = (significance, interval) => {
  {
    let significanceIcon, className;
    switch (significance) {
      case SIGNIFICANCE.POSITIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-up"
            data-tip={SIGNIFICANCE_TIPS.POSITIVE}
          />
        );
        className = "positive-significance";
        break;
      case SIGNIFICANCE.NEGATIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-down"
            data-tip={SIGNIFICANCE_TIPS.NEGATIVE}
          />
        );
        className = "negative-significance";
        break;
      case SIGNIFICANCE.NEUTRAL:
        significanceIcon = (
          <i className="fas fa-minus" data-tip={SIGNIFICANCE_TIPS.NEUTRAL} />
        );
        className = "neutral-significance";
        break;
    }

    return (
      <div className={className} data-testid={className}>
        <ReactTooltip />
        {significanceIcon}
        &nbsp;
        {interval}
      </div>
    );
  }
};

const populationField = (point, percent) => {
  return (
    <div>
      <p className="font-weight-bold">{point}</p>
      <p className="h6">{percent}%</p>
    </div>
  );
};

const countField = (lower, upper, significance) => {
  const interval = `${Math.round(lower)} to ${Math.round(upper)}`;
  return showSignificanceField(significance, interval);
};

const percentField = (lower, upper, significance) => {
  const interval = `${Math.round(lower * 1000) / 10}% to ${
    Math.round(upper * 1000) / 10
  }%`;
  return showSignificanceField(significance, interval);
};

const ResultsRow: React.FC<{ metricKey: string; results }> = ({
  metricKey,
  results,
}) => {
  const { lower, upper, point, percent, significance } = results[metricKey];

  let field;
  switch (metricKey) {
    case METRIC.USER_COUNT:
      field = populationField(point, percent);
      break;
    case METRIC.SEARCH:
      field = countField(lower, upper, significance);
      break;
    default:
      field = percentField(lower, upper, significance);
  }

  return (
    <td key={metricKey} className="align-middle">
      {field}
    </td>
  );
};

export default ResultsRow;
