import React from "react";
import ReactTooltip from "react-tooltip";

import ConfidenceInterval from "experimenter-rapid/components/visualization/ConfidenceInterval";
import {
  SIGNIFICANCE,
  METRIC,
  BRANCH_COMPARISON,
  TABLE_LABEL,
  VARIANT_TYPE,
  DISPLAY_TYPE,
} from "experimenter-rapid/components/visualization/constants/analysis";
import { SIGNIFICANCE_TIPS } from "experimenter-rapid/components/visualization/constants/tooltips";

// This is a mapping for which view on the analysis
// to display given the branch and table type.
const dataTypeMapping = {
  [TABLE_LABEL.RESULTS]: {
    [VARIANT_TYPE.CONTROL]: BRANCH_COMPARISON.ABSOLUTE,
    [VARIANT_TYPE.VARIANT]: BRANCH_COMPARISON.ABSOLUTE,
  },
  [TABLE_LABEL.HIGHLIGHTS]: {
    [VARIANT_TYPE.CONTROL]: BRANCH_COMPARISON.ABSOLUTE,
    [VARIANT_TYPE.VARIANT]: BRANCH_COMPARISON.UPLIFT,
  },
  [TABLE_LABEL.PRIMARY_METRICS]: {
    [VARIANT_TYPE.CONTROL]: BRANCH_COMPARISON.ABSOLUTE,
    [VARIANT_TYPE.VARIANT]: BRANCH_COMPARISON.ABSOLUTE,
  },
};

const showSignificanceField = (significance, interval, name, tableLabel) => {
  {
    let significanceIcon,
      changeText = "";
    const className = `${significance}-significance`;
    switch (significance) {
      case SIGNIFICANCE.POSITIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-up"
            data-tip={SIGNIFICANCE_TIPS.POSITIVE}
          />
        );
        changeText = "increased";
        break;
      case SIGNIFICANCE.NEGATIVE:
        significanceIcon = (
          <i
            className="fas fa-arrow-down"
            data-tip={SIGNIFICANCE_TIPS.NEGATIVE}
          />
        );
        changeText = "decreased";
        break;
      case SIGNIFICANCE.NEUTRAL:
        significanceIcon = (
          <i className="fas fa-minus" data-tip={SIGNIFICANCE_TIPS.NEUTRAL} />
        );
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

const conversionCountField = (totalConversions, totalUsers) => {
  return (
    <>
      <span className="font-weight-bold">
        {Math.round(totalConversions * 100) / 100}{" "}
      </span>
      / {totalUsers}
    </>
  );
};

const conversionChangeField = (lower, upper, significance) => {
  if (!lower || !upper || !significance) {
    return <div className="font-italic">---baseline---</div>;
  }

  lower = Math.round(lower * 1000) / 10;
  upper = Math.round(upper * 1000) / 10;
  return <ConfidenceInterval {...{ upper, lower, significance }} />;
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
  displayType?: DISPLAY_TYPE;
  branchComparison?: string;
}> = ({
  metricKey,
  results,
  tableLabel,
  metricName = "",
  displayType,
  branchComparison,
}) => {
  const { branch_data, is_control } = results;

  const metricData = branch_data[metricKey];
  const percent = branch_data[METRIC.USER_COUNT]["percent"];
  const userCountMetric =
    branch_data[METRIC.USER_COUNT][BRANCH_COMPARISON.ABSOLUTE]["point"];

  const branchType = is_control ? VARIANT_TYPE.CONTROL : VARIANT_TYPE.VARIANT;
  branchComparison =
    branchComparison || dataTypeMapping[tableLabel][branchType];
  const { lower, upper, point, count } = metricData[branchComparison];
  const significance = metricData["significance"];

  let field;
  switch (displayType) {
    case DISPLAY_TYPE.POPULATION:
      field = populationField(point, percent);
      break;
    case DISPLAY_TYPE.COUNT:
      field = countField(lower, upper, significance, metricName, tableLabel);
      break;
    case DISPLAY_TYPE.PERCENT:
    case DISPLAY_TYPE.CONVERSION_RATE:
      field = percentField(lower, upper, significance, metricName, tableLabel);
      break;
    case DISPLAY_TYPE.CONVERSION_COUNT:
      field = conversionCountField(count, userCountMetric);
      break;
    case DISPLAY_TYPE.CONVERSION_CHANGE:
      field = conversionChangeField(lower, upper, significance);
      break;
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
