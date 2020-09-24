import React from "react";
import { render, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import DesignInput from "experimenter/components/DesignInput";

describe("The `DesignInput` Component", () => {
  const setup = () => {
    const helpContent = "I need help";
    const labelText = "DesignInputLabel";
    const onChange = jest.fn();
    const designInput = render(
      <DesignInput
        dataTestId="designInputForm"
        helpContent={helpContent}
        label={labelText}
        onChange={onChange}
      />,
    );
    return {
      helpContent,
      labelText,
      onChange,
      designInput,
    };
  };

  it("shows the help message when help is clicked", () => {
    const { helpContent, designInput } = setup();
    const { getByText } = designInput;

    fireEvent.click(getByText("Help"));
    expect(getByText(helpContent)).not.toBeNull();
  });

  it("changes input value when new value is given", () => {
    const { designInput, onChange } = setup();
    const { getByTestId } = designInput;

    const input_text = "It's a Design Input!";
    const input = getByTestId("designInputForm");
    fireEvent.change(input, { target: { value: input_text } });
    expect(input.value).toBe(input_text);
    expect(onChange).toHaveBeenCalled();
  });
});
