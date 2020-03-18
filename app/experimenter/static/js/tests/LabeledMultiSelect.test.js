import React from "react";
import { render, fireEvent, waitForElement } from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import LabeledMultiSelect from "experimenter/components/LabeledMultiSelect";

describe("The `LabeledMultiSelect` component", () => {
  const setup = (id = "") => {
    const helpContent = "I need help";
    const labelText = "LabeledMultiSelectLabel";
    const options = [
      { value: "value1", label: "Value 1" },
      { value: "value2", label: "Value 2" },
    ];
    const onChange = jest.fn();
    const labeledMultiSelect = render(
      <LabeledMultiSelect
        helpContent={helpContent}
        id={id}
        label={labelText}
        onChange={onChange}
        options={options}
      />,
    );
    return {
      helpContent,
      labelText,
      onChange,
      labeledMultiSelect,
    };
  };

  it("shows the help message when help is clicked", () => {
    const { helpContent, labeledMultiSelect } = setup();
    const { getByText } = labeledMultiSelect;

    fireEvent.click(getByText("Help"));
    expect(getByText(helpContent)).not.toBeNull();
  });

  it("selects from the multi select", async () => {
    const { labeledMultiSelect, onChange } = setup("the-select-id");
    const { getByText, container } = labeledMultiSelect;

    const select = container.querySelector("#the-select-id");

    fireEvent.keyDown(select, { keyCode: 40 });
    await waitForElement(() => getByText("Value 2"));
    fireEvent.click(getByText("Value 2"));

    expect(onChange).toHaveBeenCalled();
  });
});
