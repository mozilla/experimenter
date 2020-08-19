import { cleanup, render, fireEvent } from "@testing-library/react";
import React from "react";
import selectEvent from "react-select-event";

import { XSelect } from "experimenter-rapid/components/forms/XSelect";

const FAKE_OPTIONS = [
  { label: "Foo", value: "foo", description: "A really nice foo", extra: 1 },
  { label: "Bar", value: "bar", description: "A really nice bar", extra: 2 },
];

afterEach(async () => {
  await cleanup();
});

function renderSelect(props = {}) {
  return render(
    <XSelect
      id="test-xselect"
      options={FAKE_OPTIONS}
      placeholder="Choose something"
      selectValue={null}
      {...props}
    />,
  );
}

function openSelect(container) {
  fireEvent.keyDown(container.querySelector("#test-xselect"), {
    keyCode: 40,
  });
}

describe("<XSelect />", () => {
  it("should render with react-select props", () => {
    const { getByText } = renderSelect();
    expect(getByText("Choose something")).toBeInTheDocument();
  });

  it("should render option labels and descriptions", async () => {
    const { container, getByText } = renderSelect();

    openSelect(container);

    expect(getByText("Foo")).toBeInTheDocument();
    expect(getByText("A really nice foo")).toBeInTheDocument();

    expect(getByText("Bar")).toBeInTheDocument();
    expect(getByText("A really nice bar")).toBeInTheDocument();
  });

  describe("onOptionChange", () => {
    it("should call onOptionChange for a single-value select", () => {
      const onOptionChange = jest.fn();

      const { container, getByText } = renderSelect({
        onOptionChange,
      });

      openSelect(container);
      fireEvent.click(getByText("Foo"));

      expect(onOptionChange).toHaveBeenCalled();
      expect(onOptionChange.mock.calls[0][0]).toEqual("foo");
    });
    it("should call onOptionChange with multi-value select", async () => {
      const onOptionChange = jest.fn();

      const { container, getByText } = renderSelect({
        onOptionChange,
        isMulti: true,
      });

      openSelect(container);
      fireEvent.click(getByText("Foo"));
      openSelect(container);
      fireEvent.click(getByText("Bar"));

      expect(onOptionChange.mock.calls[1][0]).toEqual(["foo", "bar"]);
    });

    it("should call onOptionChange with no value select", async () => {
      const onOptionChange = jest.fn();

      const { container, getByText } = renderSelect({
        onOptionChange,
        isMulti: true,
      });

      openSelect(container);
      fireEvent.click(getByText("Foo"));
      openSelect(container);
      fireEvent.click(getByText("Bar"));
      expect(onOptionChange.mock.calls[1][0]).toEqual(["foo", "bar"]);
      await selectEvent.clearFirst(getByText("Foo"));
      await selectEvent.clearFirst(getByText("Bar"));

      expect(onOptionChange.mock.calls[3][0]).toEqual(null);
    });
  });
});
