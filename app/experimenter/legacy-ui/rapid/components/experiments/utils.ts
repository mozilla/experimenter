import { XSelectOption } from "experimenter-rapid/components/forms/XSelect";

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
