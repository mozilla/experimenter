import React from "react";
import ReactTooltip from "react-tooltip";

import ConfidenceInterval from "../ConfidenceInterval";
import {
  SIGNIFICANCE,
  METRIC,
  BRANCH_COMPARISON,
  TABLE_LABEL,
  VARIANT_TYPE,
  DISPLAY_TYPE,
} from "../../lib/visualization/constants";
import { SIGNIFICANCE_TIPS } from "../../lib/visualization/constants";
import { BranchDescription } from "../../lib/visualization/types";
import { ReactComponent as SignificanceNegative } from "./significance-negative.svg";
import { ReactComponent as SignificancePositive } from "./significance-positive.svg";
import { ReactComponent as SignificanceNeutral } from "./significance-neutral.svg";

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

const showSignificanceField = (
  significance: string | undefined,
  interval: string,
  name: string,
  tableLabel: string,
) => {
  let significanceIcon,
    changeText = "";
  // Attributes set to 'undefined' don't render in the DOM
  const className = significance ? `${significance}-significance` : undefined;
  switch (significance) {
    case SIGNIFICANCE.POSITIVE:
      significanceIcon = (
        <SignificancePositive data-tip={SIGNIFICANCE_TIPS.POSITIVE} />
      );
      changeText = "increased";
      break;
    case SIGNIFICANCE.NEGATIVE:
      significanceIcon = (
        <SignificanceNegative data-tip={SIGNIFICANCE_TIPS.NEGATIVE} />
      );
      changeText = "decreased";
      break;
    case SIGNIFICANCE.NEUTRAL:
      significanceIcon = (
        <SignificanceNeutral data-tip={SIGNIFICANCE_TIPS.NEUTRAL} />
      );
      changeText = "is similar to control";
      break;
  }

  let intervalText = `(${interval} change)`;
  if (!significance) {
    intervalText = `(${interval})`;
  }

  if (tableLabel === TABLE_LABEL.HIGHLIGHTS) {
    return (
      <>
        <p {...{ className }} data-testid={className}>
          {significanceIcon}&nbsp;{name} {changeText} {intervalText}
        </p>
        <ReactTooltip />
      </>
    );
  }
  return (
    <>
      <span {...{ className }} data-testid={className}>
        {significanceIcon}&nbsp;{interval}
      </span>
      <ReactTooltip />
    </>
  );
};

const conversionCountField = (totalConversions: number, totalUsers: number) => {
  return (
    <>
      <span className="font-weight-bold">
        {Math.round(totalConversions * 100) / 100}{" "}
      </span>
      / {totalUsers}
    </>
  );
};

const conversionChangeField = (
  lower: number,
  upper: number,
  significance: string | undefined,
) => {
  if (!lower || !upper || !significance) {
    return <div className="font-italic">---baseline---</div>;
  }

  lower = Math.round(lower * 1000) / 10;
  upper = Math.round(upper * 1000) / 10;
  return <ConfidenceInterval {...{ upper, lower, significance }} />;
};

const populationField = (point: number, percent: number | undefined) => {
  return (
    <>
      <p className="font-weight-bold mb-1">{point}</p>
      <p className="mb-0">{percent}%</p>
    </>
  );
};

const countField = (
  lower: number,
  upper: number,
  significance: string | undefined,
  metricName: string,
  tableLabel: string,
) => {
  const interval = `${Math.round(lower)} to ${Math.round(upper)}`;
  return showSignificanceField(significance, interval, metricName, tableLabel);
};

const percentField = (
  lower: number,
  upper: number,
  significance: string | undefined,
  metricName: string,
  tableLabel: string,
) => {
  const interval = `${Math.round(lower * 1000) / 10}% to ${
    Math.round(upper * 1000) / 10
  }%`;
  return showSignificanceField(significance, interval, metricName, tableLabel);
};

const TableVisualizationRow: React.FC<{
  metricKey: string;
  results: BranchDescription;
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

  let field = <>{metricName} is not available</>;
  let className = "text-danger";
  if (metricData) {
    className = "";
    const percent = branch_data[METRIC.USER_COUNT]["percent"];
    const userCountMetric =
      branch_data[METRIC.USER_COUNT][BRANCH_COMPARISON.ABSOLUTE]["point"];

    const branchType = is_control ? VARIANT_TYPE.CONTROL : VARIANT_TYPE.VARIANT;
    branchComparison =
      branchComparison || dataTypeMapping[tableLabel][branchType];
    const { lower, upper, point, count } = metricData[branchComparison];
    const significance = metricData["significance"];

    switch (displayType) {
      case DISPLAY_TYPE.POPULATION:
        field = populationField(point, percent);
        break;
      case DISPLAY_TYPE.COUNT:
        field = countField(lower, upper, significance, metricName, tableLabel);
        break;
      case DISPLAY_TYPE.PERCENT:
      case DISPLAY_TYPE.CONVERSION_RATE:
        field = percentField(
          lower,
          upper,
          significance,
          metricName,
          tableLabel,
        );
        break;
      case DISPLAY_TYPE.CONVERSION_COUNT:
        field = conversionCountField(count, userCountMetric);
        break;
      case DISPLAY_TYPE.CONVERSION_CHANGE:
        field = conversionChangeField(lower, upper, significance);
        break;
    }
  }

  return tableLabel === TABLE_LABEL.HIGHLIGHTS ? (
    <div key={metricKey} {...{ className }}>
      {field}
    </div>
  ) : (
    <td key={metricKey} className={`align-middle ${className}`}>
      <div>{field}</div>
    </td>
  );
};

export default TableVisualizationRow;
