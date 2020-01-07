import React from "react";
import {
  render,
  cleanup,
  wait,
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
import { AddonDataFactory } from "./DataFactory";

describe("The `DesignForm` component for Addon", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const mockSuccessResponse = AddonDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));

    return mockSuccessResponse;
  };

  const rejectedSetUp = () => {
    const mockSuccessResponse = AddonDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    const rejectResponse = {
      data: {
        variants: [{ ratio: ["Branch sizes must be between 1 and 100."] }, {}],
      },
    };
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(mockSuccessResponse)
      .mockRejectedValueOnce(rejectResponse);
  };

  it("renders addon forms", async () => {
    const successResponse = setup();
    const { getByDisplayValue, getAllByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} isBranchedAddon={false} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });

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

  it("click on branched addon radio button", async () => {
    setup();
    const designForm = await render(<DesignForm experimentType={"addon"} />);
    const { getAllByText, getByLabelText, queryByTestId } = designForm;
    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    expect(Api.makeApiRequest).toHaveBeenCalled();
    expect(getAllByText("Signed Add-On URL")).toHaveLength(1);

    fireEvent.click(getByLabelText("Multiple add-ons"));

    expect(getAllByText("Signed Add-On URL")).toHaveLength(2);
  });

  it("removes branch 1", async () => {
    setup();
    const { getAllByText, queryByText, container } = await render(
      <DesignForm experimentType={"addon"} />,
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
      <DesignForm experimentType={"addon"} />,
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
    const { getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );
    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
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
    const { getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );
    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    fireEvent.click(getByText("Cancel Editing"));

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);
  });

  it("Make Edits to Form and is saved ", async () => {
    const data = setup();
    const { getByTestId, getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );

    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
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

    fireEvent.click(getByText("Add Branch"));

    const branch2 = getByTestId("branch2");
    const ratio2Input = within(branch2).getByTestId("Branch Size");
    fireEvent.change(ratio2Input, { target: { value: "25" } });
    const name2Input = within(branch2).getByTestId("Name");
    fireEvent.change(name2Input, { target: { value: "branch2 name" } });
    const description2Input = within(branch2).getByTestId("Description");
    fireEvent.change(description2Input, {
      target: { value: "branch2 description" },
    });

    const branch1 = getByTestId("branch1");
    const removeButton = within(branch1).getByText("Remove Branch");
    fireEvent.click(removeButton);

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

  it("Make Branch Size over 100 and Errors return", async () => {
    rejectedSetUp();
    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByTestId, getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );

    await wait(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const controlBranch = getByTestId("branch0");
    const ratio0Input = within(controlBranch).getByTestId("Branch Size");
    fireEvent.change(ratio0Input, { target: { value: "10000" } });

    fireEvent.click(getByText("Add Branch"));

    const branch2 = getByTestId("branch2");
    const ratio2Input = within(branch2).getByTestId("Branch Size");
    fireEvent.change(ratio2Input, { target: { value: "25" } });
    const name2Input = within(branch2).getByTestId("Name");
    fireEvent.change(name2Input, { target: { value: "branch2 name" } });
    const description2Input = within(branch2).getByTestId("Description");
    fireEvent.change(description2Input, {
      target: { value: "branch2 description" },
    });

    fireEvent.submit(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(ratio0Input);

    expect(
      getByText("Branch sizes must be between 1 and 100."),
    ).toBeInTheDocument();
  });
});
