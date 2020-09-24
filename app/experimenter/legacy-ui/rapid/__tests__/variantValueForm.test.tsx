import { cleanup, render, fireEvent } from "@testing-library/react";
import React from "react";

import { VariantValueForm } from "experimenter-rapid/components/forms/VariantValueForm";

afterEach(async () => {
  await cleanup();
});

describe("<VariantValueForm />", () => {
  it("should render", () => {
    const handleChange = jest.fn();
    const { getByText } = render(
      <VariantValueForm index={0} value="" onChange={handleChange} />,
    );
    expect(getByText("Value")).toBeInTheDocument();
    expect(getByText("This field accepts JSON format.")).toBeInTheDocument();
  });

  it("should call onChange when text changes ", () => {
    const handleChange = jest.fn();
    const stringifySpy = jest.spyOn(JSON, "stringify");
    const { getByDisplayValue } = render(
      <VariantValueForm
        index={0}
        value="variant value"
        onChange={handleChange}
      />,
    );

    const textArea = getByDisplayValue("variant value");
    fireEvent.focus(textArea);
    fireEvent.change(textArea, { target: { value: '{"json":"format"}' } });

    expect(handleChange).toBeCalled();
    fireEvent.blur(textArea);
    expect(stringifySpy).toBeCalled();
  });
});
