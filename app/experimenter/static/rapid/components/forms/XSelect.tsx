import React from "react";
import Select, {
  components,
  Props,
  OptionTypeBase,
  OptionProps,
  Styles,
  ValueType,
} from "react-select";

export interface XSelectOption extends OptionTypeBase {
  /** Main label for the option */
  label: string;
  /** Optional description that shows up as small text below the label */
  description?: string;
  /** Value (id) of the option */
  value: string;
}

/**
 * Custom component for each option display that shows an optional small description
 * below the label if it is defined.
 */
const OptionWithDescription = <T,>(
  props: OptionProps<T>,
): ReturnType<React.FC> => {
  const { children, data } = props;
  return (
    <div>
      <components.Option {...props}>
        {children}
        {data.description && (
          <p style={{ margin: 0 }}>
            <small style={{ opacity: 0.5, fontSize: "95%" }}>
              {data.description}
            </small>
          </p>
        )}
      </components.Option>
    </div>
  );
};

// See https://react-select.com/styles
const customStyles: Partial<Styles> = {
  container: (s) => ({
    ...s,
    lineHeight: "1.3",
  }),
};

interface XSelectCustomProps<OptionType> {
  /**
   * This is an alternative to onChange that is called with array of options as the first parameter.
   * Single selects will return a single item, multis will return the array of options
   */
  onOptionChange?: (value: Array<string> | string | null) => void;
  selectValue: string[] | string | null | void;
}

// To debug the menu dropdown, add menuIsOpen={true}
export function XSelect<OptionType extends XSelectOption = XSelectOption>(
  props: Props<OptionType> & XSelectCustomProps<OptionType>,
): ReturnType<React.FC> {
  const { selectValue, onOptionChange, ...renderProps } = props;

  // convert options to values only
  if (onOptionChange) {
    renderProps.onChange = (value: ValueType<OptionType>) => {
      let optionValues = null;
      if (value) {
        if (props.isMulti) {
          optionValues = value.map((element) => element.value);
        } else {
          optionValues = value["value"];
        }
      }

      onOptionChange(optionValues);
      renderProps.value = value;
    };
  }

  // convert values to options
  if (selectValue && props.options) {
    if (Array.isArray(props.options)) {
      let optionValue;
      if (props.isMulti) {
        optionValue = props.options.filter((element) =>
          selectValue.includes(element.value),
        );
      } else {
        optionValue = props.options.filter(
          (element) => element.value === selectValue,
        );
      }

      renderProps.value = optionValue;
    }
  }

  return (
    <Select
      components={{ Option: OptionWithDescription }}
      styles={customStyles}
      {...renderProps}
    />
  );
}
