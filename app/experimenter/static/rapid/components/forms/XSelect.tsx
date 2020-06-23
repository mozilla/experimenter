import React from "react";
import Select, {
  components,
  Props,
  OptionProps,
  Styles,
  OptionTypeBase,
  ValueType,
  ActionMeta,
} from "react-select";

export interface XSelectOption extends OptionTypeBase {
  label: string;
  value: string;
  details?: string;
}

const OptionWithDescription = (props: OptionProps<XSelectOption>) => {
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
      if (!props.onOptionChange) {
        return;
      }

      const options: Array<OptionType> = Array.isArray(value)
        ? value
        : value
        ? [value]
        : [];
      props.onOptionChange(options, action);
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
