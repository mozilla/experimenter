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
  waitForFormToLoad,
  addPrefBranch,
} from "experimenter/tests/helpers.js";
import { PrefRolloutFactory } from "experimenter/tests/DataFactory";

describe("The `DesignForm` component for Pref Rollouts", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const mockSuccessResponse = PrefRolloutFactory.build();
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));

    return mockSuccessResponse;
  };

  const rejectedSetUp = () => {
    const mockSuccessResponse = PrefRolloutFactory.build();
    const rejectResponse = {
      data: { preferences: [{ pref_name: "This field is required." }] },
    };
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(mockSuccessResponse)
      .mockRejectedValueOnce(rejectResponse);
  };

  it("renders pref rollout forms", async () => {
    setup();
    const { getAllByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalled();

    expect(getAllByText("Description")).toHaveLength(1);
    expect(getAllByText("Pref Branch")).toHaveLength(1);
  });

  it("click on pref radio button switches to pref forms", async () => {
    const mockSuccessResponse = PrefRolloutFactory.build();
    mockSuccessResponse.rollout_type = "addon";
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));
    const designForm = await render(<DesignForm experimentType={"rollout"} />);
    const { getByText, getByLabelText, container } = designForm;

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalled();
    expect(getByText("Signed Add-On URL")).toBeInTheDocument();

    fireEvent.click(getByLabelText("Pref Rollout"));

    expect(getByText("Pref Value")).toBeInTheDocument();
    expect(getByText("Pref Name")).toBeInTheDocument();
    expect(getByText("Pref Type")).toBeInTheDocument();
  });

  it("Saves and Redirects", async () => {
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
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
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);

    fireEvent.click(getByText("Cancel Editing"));

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);
  });

  it("Make Edits to Form and is saved ", async () => {
    const data = setup();
    const { getByLabelText, getAllByLabelText, getByText, container } =
      await render(<DesignForm experimentType={"rollout"} />);

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    addPrefBranch(container, 0);

    const design = "it's my design description value";
    const prefType = "boolean";
    const prefName = "browser.enabled";
    const prefValue = "false";

    const prefType2 = "boolean";
    const prefName2 = "browser.enabled";
    const prefValue2 = "false";

    const designInput = getByLabelText(/Description/);
    const prefTypeInput = getAllByLabelText(/Pref Type/);
    const prefNameInput = getAllByLabelText(/Pref Name/);
    const prefValueInput = getAllByLabelText(/Pref Value/);

    fireEvent.change(designInput, { target: { value: design } });
    fireEvent.change(prefTypeInput[0], { target: { value: prefType } });
    fireEvent.change(prefNameInput[0], { target: { value: prefName } });
    fireEvent.change(prefValueInput[0], { target: { value: prefValue } });

    fireEvent.change(prefTypeInput[1], { target: { value: prefType2 } });
    fireEvent.change(prefNameInput[1], { target: { value: prefName2 } });
    fireEvent.change(prefValueInput[1], { target: { value: prefValue2 } });

    expect(designInput.value).toBe(design);
    expect(prefTypeInput[0].value).toBe(prefType);
    expect(prefNameInput[0].value).toBe(prefName);
    expect(prefValueInput[0].value).toBe(prefValue);

    expect(prefTypeInput[1].value).toBe(prefType2);
    expect(prefNameInput[1].value).toBe(prefName2);
    expect(prefValueInput[1].value).toBe(prefValue2);

    fireEvent.submit(getByText("Save Draft and Continue"));

    const pref2 = {
      pref_type: prefType2,
      pref_name: prefName2,
      pref_value: prefValue2,
    };

    data.design = design;
    data.preferences[0].pref_type = prefType;
    data.preferences[0].pref_name = prefName;
    data.preferences[0].pref_value = prefValue;

    data.preferences.push(pref2);

    expect(Api.makeApiRequest).toBeCalledWith(expect.anything(), {
      data: data,
      method: "PUT",
    });
  });

  it("Make pref name blank, returns a required field error", async () => {
    rejectedSetUp();
    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByLabelText, getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const designInput = getByLabelText(/Description/);
    const prefNameInput = getByLabelText(/Pref Name/);

    const designValue = "it's my design description value";

    fireEvent.change(designInput, { target: { value: designValue } });
    fireEvent.change(prefNameInput, { target: { value: "" } });

    fireEvent.submit(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(prefNameInput);

    expect(getByText("This field is required.")).toBeInTheDocument();
  });
});
