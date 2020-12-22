/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { Subject as OverviewSubject } from "../components/FormOverview/mocks";
import { overviewFieldNames } from "../components/FormOverview";
import { Subject as MetricsSubject } from "../components/FormMetrics/mocks";
import { metricsFieldNames } from "../components/FormMetrics";
import { Subject as AudienceSubject } from "../components/FormAudience/mocks";
import { audienceFieldNames } from "../components/FormAudience";
import { mockExperimentQuery } from "../lib/mocks";

describe("hooks/useCommonForm", () => {
  describe("works as expected", () => {
    const overviewSetup = () => {
      const submitErrors = {
        name: ["That name is terrible, man"],
        hypothesis: ["Big bad happened"],
      };
      render(<OverviewSubject {...{ submitErrors }} />);
      return { nameField: screen.getByLabelText("Public name"), submitErrors };
    };

    it("clears submit error onChange of input field with error", async () => {
      const { nameField, submitErrors } = overviewSetup();
      const nameError = screen.getByText(submitErrors["name"][0]);
      expect(nameField).toHaveClass("is-invalid");
      expect(nameError).toBeInTheDocument();

      await act(async () => {
        fireEvent.change(nameField, {
          target: { value: "abc" },
        });
        fireEvent.blur(nameField);
      });

      expect(nameField).toHaveClass("is-valid");
      expect(nameError).not.toBeInTheDocument();
    });

    it("clears only its own field submit error onChange of field with error", async () => {
      const { nameField, submitErrors } = overviewSetup();
      const getHypothesisError = () =>
        screen.queryByText(submitErrors["hypothesis"][0]);
      const hypothesisField = screen.getByLabelText("Hypothesis");
      expect(hypothesisField).toHaveClass("is-invalid");
      expect(getHypothesisError()).toBeInTheDocument();

      await act(async () => {
        fireEvent.change(nameField, {
          target: { value: "abc" },
        });
        fireEvent.blur(nameField);
      });
      expect(hypothesisField).toHaveClass("is-invalid");
      expect(getHypothesisError()).toBeInTheDocument();
    });

    it("clears submit error onChange of multiselect", async () => {
      const submitErrors = {
        primaryProbeSetIds: ["You primary probed the wrong bear."],
      };
      const { experiment } = mockExperimentQuery("boo", {
        primaryProbeSets: [],
      });
      const { container } = render(
        <MetricsSubject {...{ submitErrors, experiment }} />,
      );

      const primaryProbeSets = screen.getByTestId("primary-probe-sets");
      const errorFeedback = screen.getByText(
        submitErrors.primaryProbeSetIds[0],
      );
      expect(errorFeedback).toBeInTheDocument();
      expect(
        container.querySelector("[for='primaryProbeSetIds'] + div"),
      ).toHaveClass("is-invalid border border-danger rounded");

      fireEvent.keyDown(primaryProbeSets.children[1], { key: "ArrowDown" });
      fireEvent.click(screen.getByText("Probe Set A"));
      expect(errorFeedback).not.toBeInTheDocument();
    });
  });

  describe("is used on expected fields", () => {
    // TODO EXP-780 - improve these tests by mocking `useCommonForm` to ensure `<FormErrors />`,
    // `formControlAttrs`, and `formSelectAttrs` are all called with the expected field names
    describe("FormOverview", () => {
      it("with experiment data", () => {
        const { experiment } = mockExperimentQuery("boo");
        render(<OverviewSubject {...{ experiment }} />);

        overviewFieldNames.forEach((name) => {
          if (name !== "application") {
            expect(
              screen.queryByTestId(`${name}-form-errors`),
            ).toBeInTheDocument();
            expect(screen.queryByTestId(name)).toBeInTheDocument();
          }
        });
      });

      it("without experiment data", async () => {
        await act(async () => {
          render(<OverviewSubject />);
        });

        overviewFieldNames.forEach((name) => {
          if (name !== "publicDescription") {
            expect(
              screen.queryByTestId(`${name}-form-errors`),
            ).toBeInTheDocument();
            expect(screen.queryByTestId(name)).toBeInTheDocument();
          }
        });
      });
    });

    it("FormMetrics", () => {
      render(<MetricsSubject />);

      metricsFieldNames.forEach((name) => {
        expect(screen.queryByTestId(`${name}-form-errors`)).toBeInTheDocument();
        // TODO EXP-780
        // expect(screen.queryByTestId(name)).toBeInTheDocument();
      });
    });

    it("FormAudience", () => {
      render(<AudienceSubject />);

      audienceFieldNames.forEach((name) => {
        expect(screen.queryByTestId(`${name}-form-errors`)).toBeInTheDocument();
        expect(screen.queryByTestId(name)).toBeInTheDocument();
      });
    });
  });
});
