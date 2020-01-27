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
import { waitForFormToLoad } from "experimenter/tests/helpers.js";
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
      data: { pref_name: ["This field is required."] },
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
    delete location.replace;
    location.replace = jest.fn();
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
    const { getByLabelText, getByText, container } = await render(
      <DesignForm experimentType={"rollout"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const design = "it's my design description value";
    const prefType = "boolean";
    const prefName = "browser.enabled";
    const prefValue = "false";

    const designInput = getByLabelText(/Description/);
    const prefTypeInput = getByLabelText(/Pref Type/);
    const prefNameInput = getByLabelText(/Pref Name/);
    const prefValueInput = getByLabelText(/Pref Value/);

    fireEvent.change(designInput, { target: { value: design } });
    fireEvent.change(prefTypeInput, { target: { value: prefType } });
    fireEvent.change(prefNameInput, { target: { value: prefName } });
    fireEvent.change(prefValueInput, { target: { value: prefValue } });

    expect(designInput.value).toBe(design);
    expect(prefTypeInput.value).toBe(prefType);
    expect(prefNameInput.value).toBe(prefName);
    expect(prefValueInput.value).toBe(prefValue);

    fireEvent.submit(getByText("Save Draft and Continue"));

    data.design = design;
    data.pref_type = prefType;
    data.pref_name = prefName;
    data.pref_value = prefValue;
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
