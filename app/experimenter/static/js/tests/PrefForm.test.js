import React from "react";
import {
  render,
  cleanup,
  waitForElement,
  fireEvent,
} from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import DesignForm from "experimenter/components/DesignForm";
import * as Api from "experimenter/utils/api";
import { PrefDataFactory } from "./DataFactory";

describe("The `DesignForm` component for Prefs", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  it("displays and edits data about single pref experiments", async () => {
    const apiResponse = PrefDataFactory.build({}, { generateVariants: 2 });
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(async () => apiResponse);

    const { getByText, getByLabelText, getAllByLabelText } = await render(
      <DesignForm
        slug="the-slug"
        experimentType={"pref"}
        isBranchedAddon={false}
      />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    // Get the fields
    const prefNameInput = await waitForElement(() =>
      getByLabelText(/Pref Name/),
    );
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
});
