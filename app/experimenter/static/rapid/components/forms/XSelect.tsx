import React from "react";
import Select, {
  components,
  Props,
  OptionTypeBase,
  OptionProps,
  Styles,
  ValueType,
  ActionMeta,
} from "react-select";

export interface XSelectOption extends OptionTypeBase {
  /** Main label for the option */
  label: string;
  /** Optional description that shows up as small text below the label */
  description?: string;
  /** Value (id) of the option */
  value: string;
}

interface OptionWithDescriptionProps extends OptionProps<XSelectOption> {
  data: XSelectOption;
}

/**
 * Custom component for each option display that shows an optional small description
 * below the label if it is defined.
 */
const OptionWithDescription: React.FC<OptionWithDescriptionProps> = (props) => {
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
   * Single selects will return a single item, multis will return the array of all options selected
   */
  onOptionChange?: (
    option: Array<OptionType>,
    action: ActionMeta<XSelectOption>,
  ) => void;
}

// To debug the menu dropdown, add menuIsOpen={true}
export function XSelect<OptionType extends XSelectOption = XSelectOption>(
  props: Props & XSelectCustomProps<OptionType>,
): ReturnType<React.FC> {
  const renderProps: Props = { ...props };
  if (props.onOptionChange) {
    renderProps.onChange = (
      value: ValueType<XSelectOption>,
      action: ActionMeta<XSelectOption>,
    ) => {
      const options: Array<OptionType> = Array.isArray(value)
        ? value
        : value
        ? [value]
        : [];
      if (props.onOptionChange) {
        props.onOptionChange(options, action);
      }
    };
  }

  return (
    <Select<XSelectOption>
      components={{ Option: OptionWithDescription }}
      styles={customStyles}
      {...renderProps}
    />
  );
}
