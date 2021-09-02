import React from "react";
import ReactTooltip from "react-tooltip";
import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  GENERAL_TIPS,
  GROUP,
  METRIC,
  SIGNIFICANCE,
  SIGNIFICANCE_TIPS,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import {
  BranchComparisonValues,
  BranchDescription,
  FormattedAnalysisPoint,
} from "../../../lib/visualization/types";
import ConfidenceInterval from "../ConfidenceInterval";
import TooltipWithMarkdown from "../TooltipWithMarkdown";
import { ReactComponent as SignificanceNegative } from "./significance-negative.svg";
import { ReactComponent as SignificanceNeutral } from "./significance-neutral.svg";
import { ReactComponent as SignificancePositive } from "./significance-positive.svg";

const BASELINE_TEXT = "(baseline)";

const showSignificanceField = (
  significance: string | undefined,
  interval: string,
  name: string,
  tableLabel: string,
  tooltip: string,
  isControlBranch: boolean,
  branchComparison?: BranchComparisonValues,
) => {
  let significanceIcon,
    changeText = "";
  // Attributes set to 'undefined' don't render in the DOM
  const className = significance ? `${significance}-significance` : undefined;
  const tooltipId = `${name}_tooltip`;
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

  // We never want to include the word "change" in absolute comparisons
  const intervalText =
    !significance || branchComparison === BRANCH_COMPARISON.ABSOLUTE
      ? `(${interval})`
      : `(${interval} change)`;

  if (tableLabel === TABLE_LABEL.HIGHLIGHTS) {
    return (
      <>
        <div {...{ className }} data-testid={className}>
          {significanceIcon}&nbsp;
          <span data-tip data-for={tooltipId}>
            {name}
          </span>
          &nbsp;
          <TooltipWithMarkdown markdown={tooltip} {...{ tooltipId }} />
          {changeText} {intervalText}
        </div>
        <ReactTooltip />
      </>
    );
  }
  return (
    <>
      <span {...{ className }} data-testid={className}>
        {significanceIcon}&nbsp;{interval}&nbsp;
        {isControlBranch && BASELINE_TEXT}
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
  range: number,
  significance: string | undefined,
) => {
  lower = Math.round(lower * 1000) / 10;
  upper = Math.round(upper * 1000) / 10;
  range = Math.round(range * 1000) / 10;
  significance = significance || SIGNIFICANCE.NEUTRAL;
  return <ConfidenceInterval {...{ upper, lower, range, significance }} />;
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
  tooltip: string,
  isControlBranch: boolean,
  branchComparison: BranchComparisonValues,
) => {
  const interval = `${lower.toFixed(2)} to ${upper.toFixed(2)}`;
  return showSignificanceField(
    significance,
    interval,
    metricName,
    tableLabel,
    tooltip,
    isControlBranch,
    branchComparison,
  );
};

const percentField = (
  lower: number,
  upper: number,
  significance: string | undefined,
  metricName: string,
  tableLabel: string,
  tooltip: string,
  isControlBranch: boolean,
  branchComparison?: BranchComparisonValues,
) => {
  const interval = `${Math.round(lower * 1000) / 10}% to ${
    Math.round(upper * 1000) / 10
  }%`;
  return showSignificanceField(
    significance,
    interval,
    metricName,
    tableLabel,
    tooltip,
    isControlBranch,
    branchComparison,
  );
};

const formattedAnalysisPointComparator = (
  a: FormattedAnalysisPoint,
  b: FormattedAnalysisPoint,
) => {
  if (!a.window_index || !b.window_index) {
    return 0;
  }
  return a.window_index - b.window_index;
};

const TableVisualizationRow: React.FC<{
  metricKey: string;
  results: BranchDescription;
  group: string;
  tableLabel: string;
  isControlBranch: boolean;
  metricName?: string;
  displayType?: DISPLAY_TYPE;
  branchComparison: BranchComparisonValues;
  tooltip?: string;
  window?: string;
  bounds?: number;
}> = ({
  metricKey,
  results,
  group,
  tableLabel,
  isControlBranch,
  metricName = "",
  displayType,
  branchComparison,
  tooltip = "",
  window = "overall",
  bounds = 0.05,
}) => {
  const { branch_data } = results;
  const metricData = branch_data[group][metricKey];
  const fieldList = [];

  let field = <>{metricName} is not available</>;
  let tooltipText =
    metricKey === METRIC.RETENTION ? GENERAL_TIPS.MISSING_RETENTION : "";
  let className = "text-danger";
  if (metricData) {
    className = "";
    tooltipText = tooltip;
    field = <div>{BASELINE_TEXT}</div>;
    const percent = branch_data[GROUP.OTHER][METRIC.USER_COUNT]["percent"];

    const userCountsList =
      branch_data[GROUP.OTHER][METRIC.USER_COUNT][BRANCH_COMPARISON.ABSOLUTE][
        "all"
      ];
    const metricDataList = metricData[branchComparison]["all"];

    userCountsList.sort(formattedAnalysisPointComparator);
    metricDataList.sort(formattedAnalysisPointComparator);

    if (metricDataList.length > 0) {
      metricDataList.forEach((dataPoint: FormattedAnalysisPoint, i: number) => {
        const { lower, upper, point, count } = dataPoint;
        const userCountMetric = userCountsList[i]["point"];
        const significance = metricData["significance"]?.[window][i + 1];

        switch (displayType) {
          case DISPLAY_TYPE.POPULATION:
            field = populationField(point!, percent);
            break;
          case DISPLAY_TYPE.COUNT:
            field = countField(
              lower!,
              upper!,
              significance,
              metricName,
              tableLabel,
              tooltipText,
              isControlBranch,
              branchComparison,
            );
            break;
          case DISPLAY_TYPE.PERCENT:
          case DISPLAY_TYPE.CONVERSION_RATE:
            field = percentField(
              lower!,
              upper!,
              significance,
              metricName,
              tableLabel,
              tooltipText,
              isControlBranch,
              branchComparison,
            );
            break;
          case DISPLAY_TYPE.CONVERSION_COUNT:
            field = conversionCountField(count!, userCountMetric!);
            break;
          case DISPLAY_TYPE.CONVERSION_CHANGE:
            field = conversionChangeField(lower!, upper!, bounds, significance);
            break;
        }
        fieldList.push({ field, tooltipText, className });
      });
      // Total number of users is present in the absolute branch comparison data. This displays
      // that number on the results table even if comparison is to the relative uplift.
    } else if (
      tableLabel === TABLE_LABEL.RESULTS &&
      branchComparison === BRANCH_COMPARISON.UPLIFT &&
      displayType === DISPLAY_TYPE.POPULATION
    ) {
      const { point } = userCountsList[0];
      field = populationField(point!, percent);
    }
  }
  /**
   * If fieldList is still empty then we either had no metric data at all, or no
   * metric data for the specific branchComparison requested.
   *
   * The former happens when there is not enough data for retention, for example.
   * The latter happens when we try to look at relative uplift for control and this
   * should fall back to "baseline".
   *
   * In either case, we need to push the current values below to be displayed.
   **/
  if (fieldList.length === 0) {
    fieldList.push({ field, tooltipText, className });
  }

  return (
    <>
      {fieldList.map((fieldData, index) => {
        const { field, tooltipText, className } = fieldData;

        return tableLabel === TABLE_LABEL.HIGHLIGHTS ? (
          <div key={metricKey} className={`${className} py-2`}>
            {field}
          </div>
        ) : (
          <td
            key={`${index}-${displayType}-${metricKey}-${tableLabel}`}
            className={`align-middle ${className}`}
            data-tip={tooltipText}
          >
            <div>{field}</div>
          </td>
        );
      })}
    </>
  );
};

export default TableVisualizationRow;
