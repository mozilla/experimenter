import React from "react";
import ReactTooltip from "react-tooltip";

import {
  SIGNIFICANCE,
  METRIC,
  BRANCH_COMPARISON,
  TABLE_LABEL,
  VARIANT_TYPE,
} from "experimenter-rapid/components/visualization/constants/analysis";
import { SIGNIFICANCE_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";

// This is a mapping for which view on the analysis
// to display given the branch and table type.
const dataTypeMapping = {
  results: {
    [VARIANT_TYPE.CONTROL]: BRANCH_COMPARISON.ABSOLUTE,
    [VARIANT_TYPE.VARIANT]: BRANCH_COMPARISON.ABSOLUTE,
  },
  highlights: {
    [VARIANT_TYPE.CONTROL]: BRANCH_COMPARISON.ABSOLUTE,
    [VARIANT_TYPE.VARIANT]: BRANCH_COMPARISON.UPLIFT,
  },
};

const showSignificanceField = (significance, interval, name, tableLabel) => {
  {
    let significanceIcon,
      className,
      changeText = "";
    switch (significance) {
      case SIGNIFICANCE.POSITIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-up"
            data-tip={SIGNIFICANCE_TIPS.POSITIVE}
          />
        );
        className = "positive-significance";
        changeText = "increased";
        break;
      case SIGNIFICANCE.NEGATIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-down"
            data-tip={SIGNIFICANCE_TIPS.NEGATIVE}
          />
        );
        className = "negative-significance";
        changeText = "decreased";
        break;
      case SIGNIFICANCE.NEUTRAL:
        significanceIcon = (
          <i className="fas fa-minus" data-tip={SIGNIFICANCE_TIPS.NEUTRAL} />
        );
        className = "neutral-significance";
        changeText = "is similar to control";
        break;
    }

    let intervalText = `(${interval} change)`;
    if (!significance) {
      intervalText = `(${interval})`;
    }

    return (
      <>
        <p className={className} data-testid={className}>
          {significanceIcon}
          &nbsp;
          {tableLabel === TABLE_LABEL.HIGHLIGHTS
            ? `${name} ${changeText} ${intervalText}`
            : `${interval}`}
        </p>
        <ReactTooltip />
      </>
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

const countField = (lower, upper, significance, metricName, tableLabel) => {
  const interval = `${Math.round(lower)} to ${Math.round(upper)}`;
  return showSignificanceField(significance, interval, metricName, tableLabel);
};

const percentField = (lower, upper, significance, metricName, tableLabel) => {
  const interval = `${Math.round(lower * 1000) / 10}% to ${
    Math.round(upper * 1000) / 10
  }%`;
  return showSignificanceField(significance, interval, metricName, tableLabel);
};

const ResultsRow: React.FC<{
  metricKey: string;
  results;
  tableLabel: string;
  metricName?: string;
}> = ({ metricKey, results, tableLabel, metricName = "" }) => {
  const { branch_data, is_control } = results;

  const metricData = branch_data[metricKey];
  const percent = branch_data[METRIC.USER_COUNT]["percent"];

  const branchType = is_control ? VARIANT_TYPE.CONTROL : VARIANT_TYPE.VARIANT;
  const branchComparison = dataTypeMapping[tableLabel][branchType];
  const { lower, upper, point } = metricData[branchComparison];
  const significance = metricData["significance"];

  let field;
  switch (metricKey) {
    case METRIC.USER_COUNT:
      field = populationField(point, percent);
      break;
    case METRIC.SEARCH:
      if (tableLabel === TABLE_LABEL.RESULTS || is_control) {
        field = countField(lower, upper, significance, metricName, tableLabel);
        break;
      }

    // fall through
    default:
      field = percentField(lower, upper, significance, metricName, tableLabel);
  }

  return (
    <>
      {tableLabel === TABLE_LABEL.HIGHLIGHTS ? (
        <div key={metricKey}>{field}</div>
      ) : (
        <td key={metricKey} className="align-middle">
          <div>{field}</div>
        </td>
      )}
    </>
  );
};

export default ResultsRow;
