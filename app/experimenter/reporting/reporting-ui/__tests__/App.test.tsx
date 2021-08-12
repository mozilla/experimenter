import '@testing-library/jest-dom';
import "@testing-library/jest-dom/extend-expect";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { act } from "react-dom/test-utils";

import App from "experimenter-reporting/components/App";

afterEach(cleanup);

describe("<App />", () => {
    it("renders reporting page", () => {
        const { getByText } = render(<App />);
        expect(getByText("Experiment Reporting")).toBeInTheDocument();
    });

    it("renders reportlog table after dates are entered", async () => {
        fetchMock.mockOnce(async () => {
            return JSON.stringify({
                /* eslint-disable @typescript-eslint/camelcase */
                data: [
                    {
                        name: "experiment name",
                        projects: "project1, project2",
                        time_in_accepted: "1:00:00",
                        time_in_draft: null,
                        time_in_live: "1:00:00",
                        time_in_preview: null,
                        time_in_review: "1:00:00",
                        time_in_ship: "1:00:00",
                        type: "Normandy-Pref",
                        url: "https://localhost/experiments/experiment-name",
                    },
                ],
                headings: [
                    "name",
                    "url",
                    "type",
                    "projects",
                    "time_in_draft",
                    "time_in_preview",
                    "time_in_review",
                    "time_in_ship",
                    "time_in_accepted",
                    "time_in_live",
                ],
                statistics: {
                    num_of_launch_by_project: { project1: 2 },
                    num_of_launches: { "Nimbus-Firefox-Desktop": 1, "Normandy-Pref": 2 },
                    status_medians: {
                        "Nimbus-Firefox-Desktop": {
                            Draft: "2:00:00",
                            Live: "2:00:00",
                            Preview: "2:00:00",
                        },
                        "Normandy-Pref": {
                            Accepted: "1:00:00",
                            Live: "1:00:00",
                            Review: "1:00:00",
                            Ship: "1:00:00",
                        },
                    },
                    total_medians: {
                        nimbus: "4:00:00",
                        normandy: "3:00:00",
                        total: "3:00:00",
                    },
                },
            }
                /* eslint-enable @typescript-eslint/camelcase */
            );

        });

        const { getByText, getByLabelText } = render(<App />);
        const startDate = getByLabelText("From:", { selector: "input" });
        fireEvent.change(startDate, { target: { value: "2020-02-02" } });
        const endDate = getByLabelText("To:", { selector: "input" });
        fireEvent.change(endDate, { target: { value: "2020-02-02" } });
        const submitButton = getByText("Submit");
        act(() => {
            fireEvent.click(submitButton);
        });
        await waitFor(() =>
            expect(getByText("experiment name")).toBeInTheDocument(),
        );
    });
});
