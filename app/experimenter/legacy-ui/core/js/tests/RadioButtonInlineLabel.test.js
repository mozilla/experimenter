import "@testing-library/jest-dom/extend-expect";
import { fireEvent, render } from "@testing-library/react";
import RadioButtonInlineLabel from "experimenter/components/RadioButtonInlineLabel";
import React from "react";

describe("The `RadioButtonInlineLabel` Component", () => {
  const setup = () => {
    const helpContent = "I need help";
    const labelText = "RadioButtonInlineLabel";
    const onChange = jest.fn();
    const radioButtonInlineLabelInput = render(
      <RadioButtonInlineLabel
        helpContent={helpContent}
        label={labelText}
        onChange={onChange}
        choices={[
          { value: "option A", label: "option A" },
          {
            value: "option B",
            label: "option B",
          },
        ]}
      />,
    );
    return {
      helpContent,
      labelText,
      onChange,
      radioButtonInlineLabelInput,
    };
  };

  it("shows the help message when help is clicked", () => {
    const { helpContent, radioButtonInlineLabelInput } = setup();
    const { getByText } = radioButtonInlineLabelInput;

    fireEvent.click(getByText("Help"));
    expect(getByText(helpContent)).not.toBeNull();
  });
});
