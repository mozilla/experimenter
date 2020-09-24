import React from "react";
import {
  render,
  cleanup,
  waitForDomChange,
  fireEvent,
} from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import DesignForm from "experimenter/components/DesignForm";
import * as Api from "experimenter/utils/api";
import {
  PrefDataFactory,
  MultiPrefDataFactory,
} from "experimenter/tests/DataFactory";
import {
  addBranch,
  removeBranch,
  waitForFormToLoad,
  addPrefBranch,
  removePrefBranch,
} from "experimenter/tests/helpers.js";

describe("The `DesignForm` component for Pref Experiments", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const apiResponse = PrefDataFactory.build({}, { generateVariants: 2 });
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(async () => apiResponse);

    return apiResponse;
  };

  const rejectedSetUp = () => {
    const apiResponse = PrefDataFactory.build({}, { generateVariants: 2 });

    const rejectApiResponse = {
      data: {
        variants: [{ ratio: ["Branch sizes must be between 1 and 100."] }, {}],
      },
    };

    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockRejectedValueOnce(rejectApiResponse);
  };

  const radioButtonSetup = () => {
    const apiResponse = PrefDataFactory.build({}, { generateVariants: 2 });

    let multiPrefApiResponse = PrefDataFactory.build(
      {},
      { generateVariants: 2 },
    );

    for (let variant of multiPrefApiResponse.variants) {
      variant["preferences"] = [{}];
    }

    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockReturnValueOnce(multiPrefApiResponse);
  };

  const radioButtonErrorSetup = () => {
    const apiResponse = PrefDataFactory.build({}, { generateVariants: 2 });
    const errorResponse = Error("Bad Request");
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockReturnValueOnce(errorResponse);
  };

  it("displays and edits data about single pref experiments", async () => {
    const apiResponse = setup();

    const {
      getByText,
      getByLabelText,
      getAllByLabelText,
      container,
    } = await render(
      <DesignForm
        slug="the-slug"
        experimentType={"pref"}
        isBranchedAddon={false}
      />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    await waitForFormToLoad(container);

    // Get the fields
    const prefNameInput = getByLabelText(/Pref Name/);
    const prefTypeInput = getByLabelText(/Pref Type/);
    const prefBranchInput = getByLabelText(/Pref Branch/);
    const branchRatioInputs = getAllByLabelText(/Branch Size/);
    const branchNameInputs = getAllByLabelText(/^\s*Name/);
    const branchDescriptionInputs = getAllByLabelText(/Description/);
    const branchValueInputs = getAllByLabelText(/Value/);

    // Check that the data returned from the server is displayed
    expect(prefNameInput.value).toBe(apiResponse.pref_name);
    expect(prefTypeInput.children[prefTypeInput.selectedIndex].innerText).toBe(
      apiResponse.pref_value,
    );
    expect(prefBranchInput.value).toBe(apiResponse.pref_branch);
    expect(branchNameInputs[0].value).toBe(apiResponse.variants[0].name);
    expect(branchNameInputs[1].value).toBe(apiResponse.variants[1].name);
    expect(branchDescriptionInputs[0].value).toBe(
      apiResponse.variants[0].description,
    );
    expect(branchDescriptionInputs[1].value).toBe(
      apiResponse.variants[1].description,
    );
    expect(branchRatioInputs[0].value).toBe(
      String(apiResponse.variants[0].ratio),
    );
    expect(branchRatioInputs[1].value).toBe(
      String(apiResponse.variants[1].ratio),
    );
    expect(branchValueInputs[0].value).toBe(
      String(apiResponse.variants[0].value),
    );
    expect(branchValueInputs[1].value).toBe(
      String(apiResponse.variants[1].value),
    );

    // Edit some fields
    fireEvent.change(prefNameInput, { target: { value: "the-new-pref-name" } });
    fireEvent.change(prefBranchInput, { target: { value: "user" } });
    fireEvent.change(prefTypeInput, { target: { value: "json string" } });
    fireEvent.change(branchValueInputs[1], {
      target: { value: "the-new-pref-value-for-branch-2" },
    });
    fireEvent.click(getByText("Save Draft and Continue"));

    // Check that the correct data was sent to the server
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    const [url, { data }] = Api.makeApiRequest.mock.calls[1];
    expect(url).toBe("experiments/the-slug/design-pref/");
    expect(data.pref_name).toBe("the-new-pref-name");
    expect(data.variants[1].value).toBe("the-new-pref-value-for-branch-2");
  });

  it("adds a branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    addBranch(container);

    expect(getAllByText("Branch Size")).toHaveLength(3);
    expect(getAllByText("Name")).toHaveLength(3);
    expect(getAllByText("Description")).toHaveLength(3);
  });

  it("removes a branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    removeBranch(container, 0);

    expect(getAllByText("Branch Size")).toHaveLength(1);
    expect(getAllByText("Name")).toHaveLength(1);
    expect(getAllByText("Description")).toHaveLength(1);
  });

  it("displays errors when branch size is over 100", async () => {
    rejectedSetUp();

    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getAllByLabelText, getByText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const firstBranchRatioInput = getAllByLabelText(/Branch Size/)[0];

    fireEvent.change(firstBranchRatioInput, { target: { value: "1000" } });

    fireEvent.click(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(firstBranchRatioInput);

    expect(
      getByText("Branch sizes must be between 1 and 100."),
    ).toBeInTheDocument();
  });

  it("changes to multipref and displays blank pref form", async () => {
    radioButtonSetup();

    const {
      getByLabelText,
      getAllByLabelText,
      getAllByText,
      container,
      getByTestId,
    } = await render(<DesignForm experimentType={"pref"} />);

    await waitForFormToLoad(container);

    fireEvent.click(getByLabelText("Different Prefs per branch"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(getByTestId("branch0"));

    expect(getAllByText("Add Pref")).toHaveLength(2);

    // blank pref forms are being displayed
    expect(getAllByLabelText(/Pref Name/)).toHaveLength(2);
    expect(getAllByLabelText(/Pref Type/)).toHaveLength(2);
    expect(getAllByLabelText(/Pref Branch/)).toHaveLength(2);
    expect(getAllByLabelText(/Pref Value/)).toHaveLength(2);
  });

  it("changes to multipref and fails", async () => {
    radioButtonErrorSetup();
    console.error = jest.fn();
    const { getByLabelText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    fireEvent.click(getByLabelText("Different Prefs per branch"));

    expect(Api.makeApiRequest).toHaveBeenCalled();
    await waitForFormToLoad(container);
    expect(console.error).toHaveBeenCalled();
  });
});

describe("The `DesignForm` component for MultiPrefs", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const apiResponse = MultiPrefDataFactory.build({}, { generateVariants: 2 });
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(async () => apiResponse);

    return apiResponse;
  };

  const rejectedSetUp = () => {
    const apiResponse = MultiPrefDataFactory.build({}, { generateVariants: 2 });

    const rejectApiResponse = {
      data: {
        variants: [
          {
            preferences: [{ pref_name: ["This field may not be blank."] }, {}],
          },
          {},
        ],
      },
    };

    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockRejectedValueOnce(rejectApiResponse);
  };

  it("displays and edits data about multi pref experiments", async () => {
    const apiResponse = setup();

    const { getByText, getAllByLabelText, container } = await render(
      <DesignForm slug="the-slug" experimentType={"pref"} isMultiPref={true} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    await waitForFormToLoad(container);

    const prefNameInputs = getAllByLabelText(/Pref Name/);
    const prefBranchInputs = getAllByLabelText(/Pref Branch/);
    const prefTypeInputs = getAllByLabelText(/Pref Type/);
    const prefValueInputs = getAllByLabelText(/Pref Value/);

    // check that two pref branches per variant are showing
    expect(prefNameInputs).toHaveLength(4);
    expect(prefNameInputs[0].value).toBe(
      apiResponse.variants[0].preferences[0].pref_name,
    );

    // Edit some fields
    fireEvent.change(prefNameInputs[0], {
      target: { value: "the-new-pref-name" },
    });
    fireEvent.change(prefBranchInputs[0], {
      target: { value: "user" },
    });
    fireEvent.change(prefTypeInputs[0], { target: { value: "json string" } });
    fireEvent.change(prefValueInputs[0], {
      target: { value: "the-new-pref-value" },
    });

    fireEvent.click(getByText("Save Draft and Continue"));

    // Check that the correct data was sent to the server
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    const [url, { data }] = Api.makeApiRequest.mock.calls[1];
    expect(url).toBe("experiments/the-slug/design-multi-pref/");
    expect(data.variants[0].preferences[0].pref_name).toBe("the-new-pref-name");
    expect(data.variants[0].preferences[0].pref_branch).toBe("user");
    expect(data.variants[0].preferences[0].pref_type).toBe("json string");
    expect(data.variants[0].preferences[0].pref_value).toBe(
      "the-new-pref-value",
    );
  });

  it("displays errors on pref branches", async () => {
    rejectedSetUp();

    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getAllByLabelText, getByText, container } = await render(
      <DesignForm slug="the-slug" experimentType={"pref"} isMultiPref={true} />,
    );

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const firstPrefBranchPrefNameInput = getAllByLabelText(/Pref Name/)[0];

    fireEvent.change(firstPrefBranchPrefNameInput, { target: { value: "" } });

    fireEvent.click(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(firstPrefBranchPrefNameInput);

    expect(getByText("This field may not be blank.")).toBeInTheDocument();
  });

  it("adds a pref", async () => {
    setup();
    const { getAllByLabelText, container } = await render(
      <DesignForm slug="the-slug" experimentType={"pref"} isMultiPref={true} />,
    );

    await waitForFormToLoad(container);

    addPrefBranch(container, 0);

    expect(getAllByLabelText(/Pref Name/)).toHaveLength(5);
  });

  it("removes a pref", async () => {
    const apiResponse = setup();
    const { queryByText, container } = await render(
      <DesignForm slug="the-slug" experimentType={"pref"} isMultiPref={true} />,
    );

    await waitForFormToLoad(container);

    removePrefBranch(container, 0, 1);

    expect(
      queryByText(apiResponse.variants[0].preferences[1].pref_name),
    ).not.toBeInTheDocument();
  });

  it("adds a branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    addBranch(container);

    expect(getAllByText("Branch Size")).toHaveLength(3);
    expect(getAllByText("Name")).toHaveLength(3);
    expect(getAllByText("Description")).toHaveLength(3);
  });

  it("removes a branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"pref"} />,
    );

    await waitForFormToLoad(container);

    removeBranch(container, 0);

    expect(getAllByText("Branch Size")).toHaveLength(1);
    expect(getAllByText("Name")).toHaveLength(1);
    expect(getAllByText("Description")).toHaveLength(1);
  });
});
