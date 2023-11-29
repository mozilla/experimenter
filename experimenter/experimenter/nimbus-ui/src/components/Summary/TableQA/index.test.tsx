/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import { Subject as BaseSubject } from "src/components/Summary/TableQA/mocks";
import { mockExperimentQuery } from "src/lib/mocks";
import { NimbusExperimentQAStatusEnum } from "src/types/globalTypes";

const Subject = ({
  onSubmit = jest.fn(),
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject {...{ onSubmit, ...props }} />
);

const qaStatus = NimbusExperimentQAStatusEnum.GREEN;
const { experiment } = mockExperimentQuery("demo-slug", {
  qaStatus: null,
});

describe("TableQA", () => {
  it("renders rows displaying required fields at experiment creation as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    const qaStatus = experiment.qaStatus;
    render(<Subject />);

    expect(screen.getByTestId("experiment-qa-status")).toHaveTextContent(
      "Not set",
    );
  });

  it("renders 'QA status' row as expected with status set", () => {
    render(<Subject {...{ qaStatus }} />);
    expect(screen.getByTestId("experiment-qa-status")).toHaveTextContent(
      "GREEN",
    );
  });
});
