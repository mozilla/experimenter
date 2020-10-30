import { XSelectOption } from "experimenter-rapid/components/forms/XSelect";
import {
  DISPLAY_TYPE,
  METRIC,
  TABLE_LABEL,
} from "experimenter-rapid/components/visualization/constants/analysis";

export const displaySelectOptionList = (
  options: XSelectOption[],
  values: string | string[],
): string[] => {
  let selectedValue: string | string[] = values;
  if (!Array.isArray(values)) {
    selectedValue = [values];
  }

  const selectedOption = options.reduce((filtered: string[], element) => {
    if (selectedValue.includes(element.value)) {
      filtered.push(element.label);
    }

    return filtered;
  }, []);
  return selectedOption;
};

export const displaySelectOptionLabels = (
  options: XSelectOption[],
  values: string | string[],
): string => {
  const selectedOption = displaySelectOptionList(options, values);
  return selectedOption.join(", ");
};

export const getTableDisplayType = (
  metricKey: string,
  tableLabel: string,
  isControl: boolean,
): DISPLAY_TYPE => {
  let displayType;
  switch (metricKey) {
    case METRIC.USER_COUNT:
      displayType = DISPLAY_TYPE.POPULATION;
      break;
    case METRIC.SEARCH:
      if (tableLabel === TABLE_LABEL.RESULTS || isControl) {
        displayType = DISPLAY_TYPE.COUNT;
        break;
      }

    // fall through
    default:
      displayType = DISPLAY_TYPE.PERCENT;
  }

  return displayType;
};
