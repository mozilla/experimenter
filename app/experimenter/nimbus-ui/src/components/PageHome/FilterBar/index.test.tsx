/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import selectEvent from "react-select-event";
import { EVERYTHING_SELECTED_VALUE, Subject } from "../mocks";

describe("FilterBar", () => {
  it("renders as expected", () => {
    render(<Subject value={EVERYTHING_SELECTED_VALUE} />);
  });

  it("reports a selection as expected", async () => {
    const expectedFirefoxVersion = "Firefox 80";
    const onChange = jest.fn();
    render(<Subject onChange={onChange} />);
    await selectEvent.select(screen.getByLabelText("Version"), [
      expectedFirefoxVersion,
    ]);
    expect(onChange).toHaveBeenCalled();
    const filterValue = onChange.mock.calls[0][0];
    expect(filterValue.firefoxVersions).toEqual(["FIREFOX_83"]);
  });

  it("selects associated applications when a feature is selected", async () => {
    const expectedFeatureConfigName = "Picture-in-Picture";
    const onChange = jest.fn();
    render(<Subject onChange={onChange} />);
    await selectEvent.select(screen.getByLabelText("Feature"), [
      expectedFeatureConfigName,
    ]);
    expect(onChange).toHaveBeenCalled();
    const filterValue = onChange.mock.calls[0][0];
    expect(filterValue.featureConfigs).toEqual(["picture-in-picture"]);
    expect(filterValue.applications).toEqual(["FENIX"]);
  });

  it("deselects associated features when an application is deselected", async () => {
    const onChange = jest.fn();
    render(
      <Subject
        onChange={onChange}
        value={{
          applications: ["DESKTOP", "IOS"],
          featureConfigs: ["maurius-odio-erat"],
        }}
      />,
    );
    await selectEvent.clearFirst(screen.getByLabelText("Application"));
    expect(onChange).toHaveBeenCalled();
    const filterValue = onChange.mock.calls[0][0];
    expect(filterValue.applications).toContain("IOS");
    expect(filterValue.applications).not.toContain("DESKTOP");
    expect(filterValue.featureConfigs).not.toContain("maurius-odio-erat");
  });
});
