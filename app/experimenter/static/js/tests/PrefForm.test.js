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
import { PrefDataFactory } from "./DataFactory";
import {
  addBranch,
  removeBranch,
  waitForFormToLoad,
} from "experimenter/tests/helpers.js";

describe("The `DesignForm` component for Prefs", () => {
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
    expect(prefNameInput.value).toBe(apiResponse.pref_key);
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
    location.replace = () => {};
    fireEvent.change(prefNameInput, { target: { value: "the-new-pref-name" } });
    fireEvent.change(branchValueInputs[1], {
      target: { value: "the-new-pref-value-for-branch-2" },
    });
    fireEvent.click(getByText("Save Draft and Continue"));

    // Check that the correct data was sent to the server
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(2);
    const [url, { data }] = Api.makeApiRequest.mock.calls[1];
    expect(url).toBe("experiments/the-slug/design-pref/");
    expect(data.pref_key).toBe("the-new-pref-name");
    expect(data.variants[1].value).toBe("the-new-pref-value-for-branch-2");
  });

  it("adds a branch", async () => {
    setup();

    const { getAllByText, container } = await render(
      <DesignForm experimentType={"addon"} />,
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
      <DesignForm experimentType={"addon"} />,
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
      <DesignForm experimentType={"addon"} />,
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
});
