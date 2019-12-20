import React from "react";
import {
  render,
  cleanup,
  waitForDomChange,
  fireEvent,
  within,
} from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import DesignForm from "experimenter/components/DesignForm";
import * as Api from "experimenter/utils/api";
import {
  addBranch,
  removeBranch,
  waitForFormToLoad,
} from "experimenter/tests/helpers.js";
import {GenericDataFactory} from "experimenter/tests/DataFactory";

describe("The `DesignForm` component for generic", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const mockSuccessResponse = GenericDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));

    return mockSuccessResponse;
  };

  const rejectedSetUp = () => {
    const mockSuccessResponse = GenericDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    const rejectResponse = {
      data: {design:["This field is required."],
      },
    };
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(mockSuccessResponse)
      .mockRejectedValueOnce(rejectResponse);
  };

  it("renders generic forms", async () => {
    const successResponse = setup();
    const { getByDisplayValue, getByText,getAllByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForFormToLoad(container);
    expect(getByText("Design")).toBeInTheDocument();
    let num_of_variants = successResponse.variants.length;
    expect(getAllByText("Branch Size")).toHaveLength(num_of_variants);
    expect(getAllByText("Name")).toHaveLength(num_of_variants);
    expect(getAllByText("Description")).toHaveLength(num_of_variants);

    for (let variant of successResponse.variants) {
      expect(getByDisplayValue(variant.name)).toBeInTheDocument();
      expect(getByDisplayValue(variant.description)).toBeInTheDocument();
      expect(getByDisplayValue(variant.ratio.toString())).toBeInTheDocument();
    }
  });



  it("removes branch 1", async () => {
    setup();
    const { getAllByText, queryByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );

    await waitForFormToLoad(container);

    removeBranch(container, 0);

    expect(queryByText("Branch 1")).toBeNull();
    // One Set of Fields for Control Branch Only
    expect(getAllByText("Branch Size")).toHaveLength(1);
    expect(getAllByText("Name")).toHaveLength(1);
    expect(getAllByText("Description")).toHaveLength(1);
  });

  it("Adds a new branch", async () => {
    setup();

    const { getAllByText, getByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );

    await waitForFormToLoad(container);

    addBranch(container);

    expect(getByText("Branch 2")).not.toBeNull();
    // 3 Sets of Fields
    expect(getAllByText("Branch Size")).toHaveLength(3);
    expect(getAllByText("Name")).toHaveLength(3);
    expect(getAllByText("Description")).toHaveLength(3);
  });

  it("Saves and Redirects", async () => {
    delete location.replace;
    location.replace = jest.fn();
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );
    await waitForFormToLoad(container);
    fireEvent.click(getByText("Save Draft and Continue"));
    expect(getByText("Save Draft and Continue")).toHaveAttribute("disabled");

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    let button = getByText("Save Draft and Continue");
    // wait for button to no longer be disabled
    await waitForDomChange({ button });
    expect(location.replace).toHaveBeenCalled();
  });

  it("Cancels and nothing is saved ", async () => {
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );
    await waitForFormToLoad(container);
    fireEvent.click(getByText("Cancel Editing"));

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);
  });

  it("Make Edits to Form and is saved ", async () => {
    const data = setup();
    const { getByTestId, getByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const controlBranch = getByTestId("branch0");
    const ratio0Input = within(controlBranch).getByTestId("Branch Size");
    fireEvent.change(ratio0Input, { target: { value: "75" } });
    const name0Input = within(controlBranch).getByTestId("Name");
    fireEvent.change(name0Input, { target: { value: "branch0 name" } });
    const description0Input = within(controlBranch).getByTestId("Description");
    fireEvent.change(description0Input, {
      target: { value: "branch0 description" },
    });

    addBranch(container);

    const branch2 = getByTestId("branch2");
    const ratio2Input = within(branch2).getByTestId("Branch Size");
    fireEvent.change(ratio2Input, { target: { value: "25" } });
    const name2Input = within(branch2).getByTestId("Name");
    fireEvent.change(name2Input, { target: { value: "branch2 name" } });
    const description2Input = within(branch2).getByTestId("Description");
    fireEvent.change(description2Input, {
      target: { value: "branch2 description" },
    });

    removeBranch(container,0);

    expect(ratio0Input.value).toBe("75");
    expect(name0Input.value).toBe("branch0 name");
    expect(description0Input.value).toBe("branch0 description");

    expect(ratio2Input.value).toBe("25");
    expect(name2Input.value).toBe("branch2 name");
    expect(description2Input.value).toBe("branch2 description");

    fireEvent.submit(getByText("Save Draft and Continue"));

    const newlyAddedBranch = {
      description: "branch2 description",
      is_control: false,
      name: "branch2 name",
      ratio: "25",
    };
    const editedControlBranch = {
      id: data.variants[0].id,
      description: "branch0 description",
      is_control: true,
      name: "branch0 name",
      ratio: "75",
    };
    data.variants = [editedControlBranch, newlyAddedBranch];
    expect(Api.makeApiRequest).toBeCalledWith(expect.anything(), {
      data: data,
      method: "PUT",
    });
  });

  it("Make Generic Blank and save returns required field error", async () => {
    rejectedSetUp();
    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByTestId, getByText, container } = await render(
      <DesignForm experimentType={"generic"} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForFormToLoad(container);


    const designValueInput = getByTestId("design");
    fireEvent.change(designValueInput, { target: { value: "" } });

    fireEvent.submit(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange("design");

    expect(
      getByText("This field is required."),
    ).toBeInTheDocument();
  });
});
