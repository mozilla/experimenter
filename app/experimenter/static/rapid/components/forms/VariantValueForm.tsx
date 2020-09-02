import React from "react";

import { Variant } from "experimenter-rapid/types/experiment";

export function VariantValueForm(props: {
  index: number;
  value: string;
  onChange: (value: string, variant: Variant, index: number) => void;
}): JSX.Element {
  const { index, value, onChange } = props;
  const [variantValue, setVariantValue] = React.useState(value);

  React.useEffect(() => {
    formatValue();
  }, []);

  const handleChange = (ev) => {
    const updatedVariantValue = ev.target.value;
    setVariantValue(updatedVariantValue);
    onChange("value", updatedVariantValue, index);
  };

  const formatValue = () => {
    try {
      setVariantValue(JSON.stringify(JSON.parse(variantValue), null, 2));
    } catch (e) {
      /* istanbul ignore next */
    }
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col">
          <label htmlFor={`variant-value-${index}`}>Value</label>
        </div>
      </div>
      <div className="row mb-2">
        <div className="col-12">
          <textarea
            className="form-control"
            id={`variant-value-${index}`}
            name="value"
            rows={4}
            value={variantValue}
            onBlur={formatValue}
            onChange={handleChange}
          />
          <small className="form-text text-muted">
            This field accepts JSON format.
          </small>
        </div>
      </div>
    </div>
  );
}
