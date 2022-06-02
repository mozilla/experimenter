import "@testing-library/jest-dom/extend-expect";
import {
  cleanup,
  fireEvent,
  render,
  waitFor,
  within,
} from "@testing-library/react";
import DesignForm from "experimenter/components/DesignForm";
import {
  AddonDataFactory,
  BranchedAddonDataFactory,
} from "experimenter/tests/DataFactory";
import {
  addBranch,
  removeBranch,
  waitForFormToLoad,
} from "experimenter/tests/helpers.js";
import * as Api from "experimenter/utils/api";
import React from "react";

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

  const badResponseSetUp = () => {
    const mockResponse = Error("A bad response has been returned");
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockResponse));
  };

  it("renders addon forms", async () => {
    const successResponse = setup();
    const {
      getAllByDisplayValue,
      getAllByText,
      getByDisplayValue,
      queryByTestId,
    } = await render(
      <DesignForm experimentType={"addon"} isBranchedAddon={false} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitFor(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });

    let num_of_variants = successResponse.variants.length;
    expect(getAllByText("Branch Size")).toHaveLength(num_of_variants);
    expect(getAllByText("Name")).toHaveLength(num_of_variants);
    expect(getAllByText("Description")).toHaveLength(num_of_variants);

    for (let variant of successResponse.variants) {
      expect(getByDisplayValue(variant.name)).toBeInTheDocument();
      expect(getByDisplayValue(variant.description)).toBeInTheDocument();
      getAllByDisplayValue(variant.ratio).map((e) =>
        expect(e).toBeInTheDocument(),
      );
    }
  });

  it("click on branched addon radio button", async () => {
    setup();
    const designForm = await render(<DesignForm experimentType={"addon"} />);
    const { getAllByText, getByLabelText, queryByTestId } = designForm;
    await waitFor(() => {
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

  it("Handles a bad Response Correctly", async () => {
    badResponseSetUp();
    console.error = jest.fn();

    await render(<DesignForm experimentType={"addon"} />);

    expect(Api.makeApiRequest).toHaveBeenCalled();
    expect(console.error).toHaveBeenCalled();
  });

  it("Saves and Redirects", async () => {
    setup();
    const { getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );
    await waitFor(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    fireEvent.click(getByText("Save Draft and Continue"));
    expect(getByText("Save Draft and Continue")).toHaveAttribute("disabled");

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    await waitFor(() => expect(location.replace).toHaveBeenCalled());
  });

  it("Saves", async () => {
    setup();
    const { getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );
    await waitFor(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    fireEvent.click(getByText("Save Draft"));
    expect(getByText("Save Draft")).toHaveAttribute("disabled");

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    await waitFor(() => expect(location.replace).toHaveBeenCalled());
  });

  it("Cancels and nothing is saved ", async () => {
    setup();
    const { getByText, queryByTestId } = await render(
      <DesignForm experimentType={"addon"} />,
    );
    await waitFor(() => {
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

    await waitFor(() => {
      expect(queryByTestId("spinner")).not.toBeInTheDocument();
    });
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const addonurlValue = "https://example.com";

    const branch0size = "75";
    const branch0name = "branch0 name";
    const branch0description = "branch0 description";

    const branch2size = "25";
    const branch2name = "branch2 name";
    const branch2description = "branch2 description";

    const addonUrlInput = getByTestId("addonUrl");
    fireEvent.change(addonUrlInput, { target: { value: addonurlValue } });

    const controlBranch = getByTestId("branch0");
    const ratio0Input = within(controlBranch).getByTestId("Branch Size");
    fireEvent.change(ratio0Input, { target: { value: branch0size } });
    const name0Input = within(controlBranch).getByTestId("Name");
    fireEvent.change(name0Input, { target: { value: branch0name } });
    const description0Input = within(controlBranch).getByTestId("Description");
    fireEvent.change(description0Input, {
      target: { value: branch0description },
    });

    fireEvent.click(getByText("Add Branch"));

    const branch2 = getByTestId("branch2");
    const ratio2Input = within(branch2).getByTestId("Branch Size");
    fireEvent.change(ratio2Input, { target: { value: branch2size } });
    const name2Input = within(branch2).getByTestId("Name");
    fireEvent.change(name2Input, { target: { value: branch2name } });
    const description2Input = within(branch2).getByTestId("Description");
    fireEvent.change(description2Input, {
      target: { value: branch2description },
    });

    const branch1 = getByTestId("branch1");
    const removeButton = within(branch1).getByText("Remove Branch");
    fireEvent.click(removeButton);

    expect(ratio0Input.value).toBe(branch0size);
    expect(name0Input.value).toBe(branch0name);
    expect(description0Input.value).toBe(branch0description);

    expect(ratio2Input.value).toBe(branch2size);
    expect(name2Input.value).toBe(branch2name);
    expect(description2Input.value).toBe(branch2description);

    fireEvent.submit(getByText("Save Draft and Continue"));

    const newlyAddedBranch = {
      description: branch2description,
      is_control: false,
      name: branch2name,
      ratio: branch2size,
    };
    const editedControlBranch = {
      id: data.variants[0].id,
      description: branch0description,
      is_control: true,
      name: branch0name,
      ratio: branch0size,
    };
    data.variants = [editedControlBranch, newlyAddedBranch];
    data.addon_release_url = addonurlValue;
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

    await waitFor(() => {
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

    await waitFor(() =>
      expect(
        getByText("Branch sizes must be between 1 and 100."),
      ).toBeInTheDocument(),
    );
  });
});

describe("The `DesignForm` component for Branched Addons", () => {
  const setup = () => {
    const apiResponse = BranchedAddonDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(async () => apiResponse);

    return apiResponse;
  };

  const rejectedSetUp = () => {
    const apiResponse = BranchedAddonDataFactory.build(
      {},
      { generateVariants: 2 },
    );

    const rejectApiResponse = {
      data: {
        variants: [{ addon_release_url: ["This field is required."] }, {}],
      },
    };

    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockRejectedValueOnce(rejectApiResponse);
  };

  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  it("displays and edits data about branched addon experiments", async () => {
    const apiResponse = setup();

    const { getByText, getAllByLabelText, container } = await render(
      <DesignForm
        slug="the-slug"
        experimentType={"addon"}
        isBranchedAddon={true}
      />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    await waitForFormToLoad(container);

    const addonUrlInputs = getAllByLabelText(/Signed Add-On URL/);

    expect(addonUrlInputs[0].value).toBe(
      apiResponse.variants[0].addon_release_url,
    );

    // Edit some fields
    location.replace = () => {};
    fireEvent.change(addonUrlInputs[0], {
      target: { value: "http://www.example.com" },
    });

    fireEvent.click(getByText("Save Draft and Continue"));

    // Check that the correct data was sent to the server
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    const [url, { data }] = Api.makeApiRequest.mock.calls[1];
    expect(url).toBe("experiments/the-slug/design-branched-addon/");
    expect(data.variants[0].addon_release_url).toBe("http://www.example.com");
  });

  it("displays errors on branched addon variants", async () => {
    rejectedSetUp();

    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByText, getAllByLabelText, container } = await render(
      <DesignForm
        slug="the-slug"
        experimentType={"addon"}
        isBranchedAddon={true}
      />,
    );

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const firstAddonUrlInput = getAllByLabelText(/Signed Add-On URL/)[0];

    fireEvent.change(firstAddonUrlInput, { target: { value: "" } });

    fireEvent.click(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitFor(() =>
      expect(getByText("This field is required.")).toBeInTheDocument(),
    );
  });

  it("adds a `branchedAddon` branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"addon"} isBranchedAddon={true} />,
    );

    await waitForFormToLoad(container);

    addBranch(container);

    expect(getAllByText(/Signed Add-On URL/)).toHaveLength(3);
  });

  it("removes a `branchedAddon` branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"addon"} isBranchedAddon={true} />,
    );

    await waitForFormToLoad(container);

    removeBranch(container, 0);

    expect(getAllByText(/Signed Add-On URL/)).toHaveLength(1);
  });
});
