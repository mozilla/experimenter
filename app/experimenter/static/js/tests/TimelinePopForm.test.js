import React from "react";
import {
  render,
  cleanup,
  waitForDomChange,
  fireEvent,
} from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import TimelinePopForm from "experimenter/components/TimelinePopForm";
import * as Api from "experimenter/utils/api";
import { TimelinePopDataFactory } from "experimenter/tests/DataFactory";
import { waitForFormToLoad } from "experimenter/tests/helpers.js";

describe("The TimelinePopForm component for experiments", () => {
  afterEach(() => {
    Api.makeApiRequest.mockClear();
    cleanup();
  });

  const setup = () => {
    const apiResponse = TimelinePopDataFactory.build();
    jest
      .spyOn(Api, "makeApiRequest")
      .mockImplementation(async () => apiResponse);

    return apiResponse;
  };

  const rejectedSetUp = () => {
    const apiResponse = TimelinePopDataFactory.build();

    const rejectApiResponse = {
      data: {
        firefox_max_version: [
          "The max version must be larger than or equal to the min version.",
        ],
      },
    };

    jest
      .spyOn(Api, "makeApiRequest")
      .mockReturnValueOnce(apiResponse)
      .mockRejectedValueOnce(rejectApiResponse);
  };

  const apiErrorSetup = () => {
    const errorResponse = Error("Bad Request");
    jest.spyOn(Api, "makeApiRequest").mockReturnValueOnce(errorResponse);
  };

  it("displays and edits timeline and population data", async () => {
    const apiResponse = setup();

    const { getByLabelText, getByText, container } = await render(
      <TimelinePopForm
        experimentType="pref"
        slug="the-slug"
        shouldHavePopPercent={"True"}
      />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    await waitForFormToLoad(container);

    const proposedStartDateInput = getByLabelText(/Proposed Start Date/);
    const proposedEnrollmentInput = getByLabelText(
      /Proposed Enrollment Duration/,
    );
    const proposedDurationInput = getByLabelText(/Proposed Total Duration/);
    const populationPercentInput = getByLabelText(/Population Percentage/);
    const firefoxMinVersionInput = getByLabelText(/Firefox Min Version/);
    const firefoxMaxVersionInput = getByLabelText(/Firefox Max Version/);
    const clientMatchingInput = getByLabelText(/Population Filtering/);
    const channelInput = getByLabelText(/Firefox Channel/);
    const countriesInput = container.querySelector("#id_countries");
    const platformsInput = container.querySelector("#id_platforms");
    const windowsVersionsInput = container.querySelector(
      "#id_windows_versions input",
    );
    const newProfilesOnlyInput = getByLabelText(/New Profiles Only/);
    expect(proposedStartDateInput.value).toBe(apiResponse.proposed_start_date);
    expect(firefoxMinVersionInput.value).toBe(apiResponse.firefox_min_version);
    expect(firefoxMaxVersionInput.value).toBe(apiResponse.firefox_max_version);

    // check that windows versions input isn't enabled because multiple
    // platforms are selected.
    expect(windowsVersionsInput).toBeDisabled();

    //edit some Fields
    fireEvent.change(proposedStartDateInput, { target: { value: "" } });
    fireEvent.change(proposedEnrollmentInput, { target: { value: "50" } });
    fireEvent.change(proposedDurationInput, { target: { value: "" } });
    fireEvent.change(populationPercentInput, { target: { value: "50.0000" } });
    fireEvent.change(firefoxMinVersionInput, { target: { value: "60.0" } });
    fireEvent.change(firefoxMaxVersionInput, { target: { value: "64.0" } });
    fireEvent.change(channelInput, { target: { value: "Nightly" } });
    fireEvent.change(clientMatchingInput, {
      target: { value: "different filtering" },
    });
    fireEvent.click(newProfilesOnlyInput);

    // delete option from multiselects
    fireEvent.keyDown(countriesInput, { keyCode: 46 });
    fireEvent.keyDown(platformsInput, { keyCode: 46 });

    // check that windows versions is now enabled because only "windows"
    // is selected for platforms.
    expect(windowsVersionsInput).toBeEnabled();

    fireEvent.click(getByText("Save Draft"));

    // Check that the correct data was sent to the server
    const [url, { data }] = Api.makeApiRequest.mock.calls[1];

    expect(url).toBe("experiments/the-slug/timeline-population/");
    expect(data.proposed_start_date).toBe(null);
    expect(data.proposed_enrollment).toBe("50");
    expect(data.proposed_duration).toBe(null);
    expect(data.population_percent).toBe("50.0000");
    expect(data.firefox_min_version).toBe("60.0");
    expect(data.firefox_max_version).toBe("64.0");
    expect(data.platforms).toEqual([
      { value: "All Windows", label: "Windows" },
    ]);
    expect(data.client_matching).toBe("different filtering");
    expect(data.countries).toEqual([]);
    expect(data.profile_age).toBe("New Profiles Only");
  });

  it("displays errors on firefox version errors", async () => {
    rejectedSetUp();

    let scrollIntoViewMock = jest.fn();

    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const { getByLabelText, getByText, container } = await render(
      <TimelinePopForm slug="the-slug" experimentType="pref" />,
    );

    await waitForFormToLoad(container);

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    const firefoxMinVersionInput = getByLabelText(/Firefox Min Version/);
    const firefoxMaxVersionInput = getByLabelText(/Firefox Max Version/);

    fireEvent.change(firefoxMinVersionInput, { target: { value: "70.0" } });
    fireEvent.change(firefoxMaxVersionInput, { target: { value: "64.0" } });

    fireEvent.click(getByText("Save Draft and Continue"));

    expect(Api.makeApiRequest).toHaveBeenCalled();

    await waitForDomChange(firefoxMaxVersionInput);

    expect(
      getByText(
        "The max version must be larger than or equal to the min version.",
      ),
    ).toBeInTheDocument();
  });

  it("logs failure of api call", async () => {
    apiErrorSetup();
    console.error = jest.fn();
    await render(<TimelinePopForm slug="the-slug" />);

    expect(Api.makeApiRequest).toHaveBeenCalled();
    expect(console.error).toHaveBeenCalled();
  });

  it("displays and edit rollout playbook on rollout delivery", async () => {
    setup();

    const { getByLabelText, getByText, container } = await render(
      <TimelinePopForm
        experimentType="rollout"
        slug="the-slug"
        shouldHavePopPercent={"True"}
      />,
    );

    expect(Api.makeApiRequest).toHaveBeenCalledTimes(1);

    await waitForFormToLoad(container);

    const rolloutPlaybookInput = getByLabelText(/Rollout Playbook/);

    fireEvent.change(rolloutPlaybookInput, {
      target: { value: "low_risk" },
    });
    fireEvent.click(getByText("Save Draft"));

    const [url, { data }] = Api.makeApiRequest.mock.calls[1];
    expect(url).toBe("experiments/the-slug/timeline-population/");
    expect(data.rollout_playbook).toBe("low_risk");
  });
});
