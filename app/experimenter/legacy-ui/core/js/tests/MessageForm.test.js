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
import { MessageDataFactory } from "experimenter/tests/DataFactory";
import {
  MESSAGE_TEMPLATE_DOOR_LABEL,
  MESSAGE_TEMPLATE_DOOR,
  MESSAGE_TYPE_CFR_LABEL,
  MESSAGE_TYPE_CFR,
  MESSAGE_TYPE_WELCOME_LABEL,
  MESSAGE_TYPE_WELCOME,
} from "experimenter/components/constants";

describe("The `DesignForm` component for message", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const mockSuccessResponse = MessageDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(() => Promise.resolve(mockSuccessResponse));

    return mockSuccessResponse;
  };

  const rejectedSetUp = () => {
    const mockSuccessResponse = MessageDataFactory.build(
      {},
      { generateVariants: 2 },
    );
    const rejectResponse = {
      data: { message_type: ["This field is required."] },
    };
    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(mockSuccessResponse)
      .mockRejectedValueOnce(rejectResponse);
  };

  it("Renders cfr message form", async () => {
    const successResponse = setup();
    const { container, getAllByText, getByLabelText, getByText } = await render(
      <DesignForm experimentType={"message"} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForFormToLoad(container);

    fireEvent.click(getByLabelText(MESSAGE_TYPE_CFR_LABEL));

    expect(
      getByText("What message type does this experiment use?"),
    ).toBeInTheDocument();

    let num_of_variants = successResponse.variants.length;

    expect(getAllByText("Branch Size")).toHaveLength(num_of_variants);
    expect(getAllByText("Name")).toHaveLength(num_of_variants);
    expect(getAllByText("Description")).toHaveLength(num_of_variants);
    expect(getAllByText("Message Targeting")).toHaveLength(num_of_variants);
    expect(getAllByText("Message Threshold")).toHaveLength(num_of_variants);
    expect(getAllByText("Message Triggers")).toHaveLength(num_of_variants);
    expect(getAllByText("Message Content")).toHaveLength(num_of_variants);
  });

  it("Renders about:welcome message form", async () => {
    const successResponse = setup();
    const { container, getAllByText, getByLabelText, getByText } = await render(
      <DesignForm experimentType={"message"} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForFormToLoad(container);

    fireEvent.click(getByLabelText(MESSAGE_TYPE_WELCOME_LABEL));

    expect(
      getByText("What message type does this experiment use?"),
    ).toBeInTheDocument();

    let num_of_variants = successResponse.variants.length;

    expect(getAllByText("Branch Size")).toHaveLength(num_of_variants);
    expect(getAllByText("Name")).toHaveLength(num_of_variants);
    expect(getAllByText("Description")).toHaveLength(num_of_variants);
    expect(getAllByText("Message Content")).toHaveLength(num_of_variants);
  });

  it("Make edits to cfr form and is saved ", async () => {
    const data = setup();
    const { getByTestId, getByLabelText, getByText, container } = await render(
      <DesignForm experimentType={"message"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    fireEvent.click(getByLabelText(MESSAGE_TYPE_CFR_LABEL));
    fireEvent.click(getByLabelText(MESSAGE_TEMPLATE_DOOR_LABEL));

    const branch0ratio = "75";
    const branch0name = "branch0 name";
    const branch0description = "branch0 description";
    const branch0messageTargeting = "branch0 targeting";
    const branch0messageThreshold = "branch0 threshold";
    const branch0messageTriggers = "branch0 triggers";
    const branch0messageContent = "branch0 content";

    const branch2ratio = "25";
    const branch2name = "branch2 name";
    const branch2description = "branch2 description";
    const branch2messageTargeting = "branch2 targeting";
    const branch2messageThreshold = "branch2 threshold";
    const branch2messageTriggers = "branch2 triggers";
    const branch2messageContent = "branch2 content";

    const controlBranch = getByTestId("branch0");

    const ratio0Input = within(controlBranch).getByTestId("Branch Size");
    const name0Input = within(controlBranch).getByTestId("Name");
    const description0Input = within(controlBranch).getByTestId("Description");
    const messageTargeting0Input =
      within(controlBranch).getByTestId("Message Targeting");
    const messageThreshold0Input =
      within(controlBranch).getByTestId("Message Threshold");
    const messageTriggers0Input =
      within(controlBranch).getByTestId("Message Triggers");
    const messageContent0Input =
      within(controlBranch).getByTestId("Message Content");

    fireEvent.change(ratio0Input, { target: { value: branch0ratio } });
    fireEvent.change(name0Input, { target: { value: branch0name } });
    fireEvent.change(description0Input, {
      target: { value: branch0description },
    });
    fireEvent.change(messageTargeting0Input, {
      target: { value: branch0messageTargeting },
    });
    fireEvent.change(messageThreshold0Input, {
      target: { value: branch0messageThreshold },
    });
    fireEvent.change(messageTriggers0Input, {
      target: { value: branch0messageTriggers },
    });
    fireEvent.change(messageContent0Input, {
      target: { value: branch0messageContent },
    });

    addBranch(container);

    const branch2 = getByTestId("branch2");

    const ratio2Input = within(branch2).getByTestId("Branch Size");
    const name2Input = within(branch2).getByTestId("Name");
    const description2Input = within(branch2).getByTestId("Description");
    const messageTargeting2Input =
      within(branch2).getByTestId("Message Targeting");
    const messageThreshold2Input =
      within(branch2).getByTestId("Message Threshold");
    const messageTriggers2Input =
      within(branch2).getByTestId("Message Triggers");
    const messageContent2Input = within(branch2).getByTestId("Message Content");

    fireEvent.change(ratio2Input, { target: { value: branch2ratio } });
    fireEvent.change(name2Input, { target: { value: branch2name } });
    fireEvent.change(description2Input, {
      target: { value: branch2description },
    });
    fireEvent.change(messageTargeting2Input, {
      target: { value: branch2messageTargeting },
    });
    fireEvent.change(messageThreshold2Input, {
      target: { value: branch2messageThreshold },
    });
    fireEvent.change(messageTriggers2Input, {
      target: { value: branch2messageTriggers },
    });
    fireEvent.change(messageContent2Input, {
      target: { value: branch2messageContent },
    });

    removeBranch(container, 0);

    expect(ratio0Input.value).toBe(branch0ratio);
    expect(name0Input.value).toBe(branch0name);
    expect(description0Input.value).toBe(branch0description);
    expect(messageTargeting0Input.value).toBe(branch0messageTargeting);
    expect(messageThreshold0Input.value).toBe(branch0messageThreshold);
    expect(messageTriggers0Input.value).toBe(branch0messageTriggers);
    expect(messageContent0Input.value).toBe(branch0messageContent);

    expect(ratio2Input.value).toBe(branch2ratio);
    expect(name2Input.value).toBe(branch2name);
    expect(description2Input.value).toBe(branch2description);
    expect(messageTargeting2Input.value).toBe(branch2messageTargeting);
    expect(messageThreshold2Input.value).toBe(branch2messageThreshold);
    expect(messageTriggers2Input.value).toBe(branch2messageTriggers);
    expect(messageContent2Input.value).toBe(branch2messageContent);

    fireEvent.submit(getByText("Save Draft and Continue"));

    const newlyAddedBranch = {
      is_control: false,
      ratio: branch2ratio,
      name: branch2name,
      description: branch2description,
      message_targeting: branch2messageTargeting,
      message_threshold: branch2messageThreshold,
      message_triggers: branch2messageTriggers,
      value: branch2messageContent,
    };

    const editedControlBranch = {
      id: data.variants[0].id,
      is_control: true,
      ratio: branch0ratio,
      name: branch0name,
      description: branch0description,
      message_targeting: branch0messageTargeting,
      message_threshold: branch0messageThreshold,
      message_triggers: branch0messageTriggers,
      value: branch0messageContent,
    };

    data.variants = [editedControlBranch, newlyAddedBranch];
    data.message_type = MESSAGE_TYPE_CFR;
    data.message_template = MESSAGE_TEMPLATE_DOOR;
    expect(Api.makeApiRequest).toBeCalledWith(expect.anything(), {
      data: data,
      method: "PUT",
    });
  });

  it("Make edits to about:welcome form and is saved ", async () => {
    const data = setup();
    const { getByTestId, getByLabelText, getByText, container } = await render(
      <DesignForm experimentType={"message"} />,
    );

    await waitForFormToLoad(container);
    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    fireEvent.click(getByLabelText(MESSAGE_TYPE_WELCOME_LABEL));

    const branch0ratio = "75";
    const branch0name = "branch0 name";
    const branch0description = "branch0 description";
    const branch0messageContent = "branch0 content";

    const branch2ratio = "25";
    const branch2name = "branch2 name";
    const branch2description = "branch2 description";
    const branch2messageContent = "branch2 content";

    const controlBranch = getByTestId("branch0");

    const ratio0Input = within(controlBranch).getByTestId("Branch Size");
    const name0Input = within(controlBranch).getByTestId("Name");
    const description0Input = within(controlBranch).getByTestId("Description");
    const messageContent0Input =
      within(controlBranch).getByTestId("Message Content");

    fireEvent.change(ratio0Input, { target: { value: branch0ratio } });
    fireEvent.change(name0Input, { target: { value: branch0name } });
    fireEvent.change(description0Input, {
      target: { value: branch0description },
    });
    fireEvent.change(messageContent0Input, {
      target: { value: branch0messageContent },
    });

    addBranch(container);

    const branch2 = getByTestId("branch2");

    const ratio2Input = within(branch2).getByTestId("Branch Size");
    const name2Input = within(branch2).getByTestId("Name");
    const description2Input = within(branch2).getByTestId("Description");
    const messageContent2Input = within(branch2).getByTestId("Message Content");

    fireEvent.change(ratio2Input, { target: { value: branch2ratio } });
    fireEvent.change(name2Input, { target: { value: branch2name } });
    fireEvent.change(description2Input, {
      target: { value: branch2description },
    });
    fireEvent.change(messageContent2Input, {
      target: { value: branch2messageContent },
    });

    removeBranch(container, 0);

    expect(ratio0Input.value).toBe(branch0ratio);
    expect(name0Input.value).toBe(branch0name);
    expect(description0Input.value).toBe(branch0description);
    expect(messageContent0Input.value).toBe(branch0messageContent);

    expect(ratio2Input.value).toBe(branch2ratio);
    expect(name2Input.value).toBe(branch2name);
    expect(description2Input.value).toBe(branch2description);
    expect(messageContent2Input.value).toBe(branch2messageContent);

    fireEvent.submit(getByText("Save Draft and Continue"));

    const newlyAddedBranch = {
      is_control: false,
      ratio: branch2ratio,
      name: branch2name,
      description: branch2description,
      value: branch2messageContent,
    };

    const editedControlBranch = {
      id: data.variants[0].id,
      is_control: true,
      ratio: branch0ratio,
      name: branch0name,
      description: branch0description,
      value: branch0messageContent,
    };

    data.variants = [editedControlBranch, newlyAddedBranch];
    data.message_type = MESSAGE_TYPE_WELCOME;
    expect(Api.makeApiRequest).toBeCalledWith(expect.anything(), {
      data: data,
      method: "PUT",
    });
  });

  it("Removes a branch", async () => {
    setup();
    const { getAllByText, queryByText, container } = await render(
      <DesignForm experimentType={"message"} />,
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
      <DesignForm experimentType={"message"} />,
    );

    await waitForFormToLoad(container);

    addBranch(container);

    expect(getByText("Branch 2")).not.toBeNull();
    // 3 Sets of Fields
    expect(getAllByText("Branch Size")).toHaveLength(3);
    expect(getAllByText("Name")).toHaveLength(3);
    expect(getAllByText("Description")).toHaveLength(3);
  });

  it("Saves and redirects", async () => {
    setup();
    const { getByText, container } = await render(
      <DesignForm experimentType={"message"} />,
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
      <DesignForm experimentType={"message"} />,
    );
    await waitForFormToLoad(container);
    fireEvent.click(getByText("Cancel Editing"));

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);
  });

  it("Blank form displays field error", async () => {
    rejectedSetUp();
    let scrollIntoViewMock = jest.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByText, container } = await render(
      <DesignForm experimentType={"message"} />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForFormToLoad(container);

    fireEvent.submit(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange("message_type");

    expect(getByText("This field is required.")).toBeInTheDocument();
  });
});
