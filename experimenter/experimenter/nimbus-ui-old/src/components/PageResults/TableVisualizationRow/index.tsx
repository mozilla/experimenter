import React, { useContext } from "react";
import ReactTooltip from "react-tooltip";
import ConfidenceInterval from "src/components/PageResults/ConfidenceInterval";
import { ReactComponent as SignificanceNegative } from "src/components/PageResults/TableVisualizationRow/significance-negative.svg";
import { ReactComponent as SignificanceNeutral } from "src/components/PageResults/TableVisualizationRow/significance-neutral.svg";
import { ReactComponent as SignificancePositive } from "src/components/PageResults/TableVisualizationRow/significance-positive.svg";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { ResultsContext } from "src/lib/contexts";
import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  GENERAL_TIPS,
  GROUP,
  METRIC,
  SIGNIFICANCE,
  SIGNIFICANCE_TIPS,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import {
  BranchComparisonValues,
  BranchDescription,
  FormattedAnalysisPoint,
} from "src/lib/visualization/types";

const BASELINE_TEXT = "(baseline)";

const showSignificanceField = (
  significance: string | undefined,
  interval: string,
  fullInterval: string,
  name: string,
  tableLabel: string,
  tooltip: string,
  isControlBranch: boolean,
  referenceBranch: string,
  branchComparison?: BranchComparisonValues,
) => {
  let significanceIcon,
    changeText = "";
  // Attributes set to 'undefined' don't render in the DOM
  const className = significance ? `${significance}-significance` : undefined;
  const tooltipId = `${name}_tooltip`;
  const intervalTooltipId = `${name}_${fullInterval.replaceAll(
    " ",
    "_",
  )}_interval_tooltip`;
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
      changeText = `is similar to ${referenceBranch}`;
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
          {changeText}
          &nbsp;
          <span data-tip data-for={intervalTooltipId}>
            {intervalText}
          </span>
          <ReactTooltip id={intervalTooltipId}>{fullInterval}</ReactTooltip>
        </div>
        <ReactTooltip />
      </>
    );
  }
  return (
    <>
      <span {...{ className }} data-testid={className}>
        {significanceIcon}&nbsp;
        <span data-tip data-for={intervalTooltipId}>
          {interval} {isControlBranch && BASELINE_TEXT}
        </span>
        &nbsp;
        <ReactTooltip id={intervalTooltipId}>{fullInterval}</ReactTooltip>
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
  referenceBranch: string,
) => {
  const tooltip = `${Math.round(lower * 100000000) / 1000000}% to ${
    Math.round(upper * 100000000) / 1000000
  }%`;
  lower = Math.round(lower * 1000) / 10;
  upper = Math.round(upper * 1000) / 10;
  range = Math.round(range * 1000) / 10;
  significance = significance || SIGNIFICANCE.NEUTRAL;
  return (
    <ConfidenceInterval
      {...{ upper, lower, range, significance, referenceBranch, tooltip }}
    />
  );
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
  referenceBranch: string,
  branchComparison: BranchComparisonValues,
) => {
  const interval = `${lower ? lower.toFixed(2) : lower} to ${
    upper ? upper.toFixed(2) : upper
  }`;
  const fullInterval =
    lower && upper ? `${lower.toFixed(6)} to ${upper.toFixed(6)}` : "";
  return showSignificanceField(
    significance,
    interval,
    fullInterval,
    metricName,
    tableLabel,
    tooltip,
    isControlBranch,
    referenceBranch,
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
  referenceBranch: string,
  branchComparison?: BranchComparisonValues,
) => {
  const interval = `${Math.round(lower * 1000) / 10}% to ${
    Math.round(upper * 1000) / 10
  }%`;
  const fullInterval =
    lower && upper
      ? `${Math.round(lower * 100000000) / 1000000}% to ${
          Math.round(upper * 100000000) / 1000000
        }%`
      : "";
  return showSignificanceField(
    significance,
    interval,
    fullInterval,
    metricName,
    tableLabel,
    tooltip,
    isControlBranch,
    referenceBranch,
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
  referenceBranch: string;
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
  referenceBranch = "",
}) => {
  const { branch_data } = results;
  const metricData = branch_data[group][metricKey];
  const fieldList = [];
  const { controlBranchName } = useContext(ResultsContext);

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
    const metricDataList =
      branchComparison === BRANCH_COMPARISON.ABSOLUTE
        ? metricData[branchComparison]["all"]
        : metricData[branchComparison][referenceBranch]?.["all"];

    if (metricDataList && metricDataList.length > 0) {
      userCountsList.sort(formattedAnalysisPointComparator);
      metricDataList.sort(formattedAnalysisPointComparator);

      metricDataList.forEach((dataPoint: FormattedAnalysisPoint, i: number) => {
        const { lower, upper, point, count } = dataPoint;
        const userCountMetric = userCountsList[i]["point"];
        const significanceIndex = `${i + 1}`;
        const significance =
          metricData["significance"]?.[referenceBranch]?.[window]?.[
            significanceIndex
          ];

        switch (displayType) {
          case DISPLAY_TYPE.POPULATION:
            field = populationField(point!, percent);
            break;
          case DISPLAY_TYPE.COUNT:
            field = countField(
              lower!,
              upper!,
              significance,
              metricName || metricKey,
              tableLabel,
              tooltipText,
              isControlBranch,
              referenceBranch,
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
              referenceBranch,
              branchComparison,
            );
            break;
          case DISPLAY_TYPE.CONVERSION_COUNT:
            field = conversionCountField(count!, userCountMetric!);
            break;
          case DISPLAY_TYPE.CONVERSION_CHANGE:
            field = conversionChangeField(
              lower!,
              upper!,
              bounds,
              significance,
              referenceBranch,
            );
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
      fieldList.push({ field, tooltipText, className });
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
   *
   * **Addition to above**
   * A new case where this can happen is when the user has selected a non-control
   * reference branch, but the experiment does not have pairwise branch comparison
   * results. This means that there will be nothing to display for the branches
   * as they compare to the selected reference branch.
   *
   * For this case, the display should be similar to the relative uplift for control,
   * but with a different message to clarify that it is not baseline.
   **/
  if (fieldList.length === 0) {
    if (
      branchComparison !== BRANCH_COMPARISON.ABSOLUTE &&
      referenceBranch !== controlBranchName &&
      !isControlBranch
    ) {
      field = <div>(results not available)</div>;
      tooltipText =
        "This is likely because pairwise branch comparison results are not available for this experiment. Please select the experiment's configured control branch to view available results, or contact #ask-experimenter to request that analysis be rerun to get pairwise branch comparison results.";
      className = "text-danger";
    }
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
