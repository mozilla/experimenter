/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import React from "react";
import { DOCUMENTATION_LINKS_TOOLTIP } from ".";
import { FIELD_MESSAGES } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { NimbusDocumentationLinkTitle } from "../../types/globalTypes";
import { Subject } from "./mocks";

describe("FormOverview", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await act(async () =>
      expect(screen.getByTestId("FormOverview")).toBeInTheDocument(),
    );
  });

  it("calls onCancel when cancel clicked", async () => {
    const onCancel = jest.fn();
    render(<Subject {...{ onCancel }} />);

    const cancelButton = screen.getByText("Cancel");
    await act(async () => void fireEvent.click(cancelButton));
    expect(onCancel).toHaveBeenCalled();
  });

  it("renders initial documentation links", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      documentationLinks: [
        {
          __typename: "NimbusDocumentationLinkType",
          title: NimbusDocumentationLinkTitle.DESIGN_DOC,
          link: "https://mozilla.com",
        },
        {
          __typename: "NimbusDocumentationLinkType",
          title: NimbusDocumentationLinkTitle.DS_JIRA,
          link: "https://mozilla.com",
        },
      ],
    });
    render(<Subject {...{ experiment }} />);
    const tooltip = await screen.findByTestId("tooltip-documentation-links");
    expect(tooltip).toHaveAttribute("data-tip", DOCUMENTATION_LINKS_TOOLTIP);
    const linkEls = await screen.findAllByTestId("DocumentationLink");
    expect(linkEls).toHaveLength(experiment.documentationLinks!.length);
    linkEls.forEach((linkEl, index) => {
      const selected = linkEl.querySelector(
        "option[selected]",
      ) as HTMLSelectElement;
      expect(selected.value).toEqual(
        experiment.documentationLinks![index].title,
      );
    });
  });

  const fillOutNewForm = async (expected: Record<string, string>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Application", expected.application],
    ]) {
      const fieldName = screen.getByLabelText(labelText);

      await act(async () => {
        fireEvent.click(fieldName);
        fireEvent.blur(fieldName);
      });
      if (labelText !== "Hypothesis") {
        expect(fieldName).toHaveClass("is-invalid");
        expect(fieldName).not.toHaveClass("is-valid");
      }

      await act(async () => {
        fireEvent.change(fieldName, { target: { value: fieldValue } });
        fireEvent.blur(fieldName);
      });
      expect(fieldName).not.toHaveClass("is-invalid");
      expect(fieldName).toHaveClass("is-valid");
    }
  };

  const getDocumentationLinkFields = (index: number) => {
    const testIdBase = `documentationLinks[${index}]`;
    const titleField = screen.getByTestId(
      `${testIdBase}.title`,
    ) as HTMLInputElement;
    const linkField = screen.getByTestId(
      `${testIdBase}.link`,
    ) as HTMLInputElement;
    const removeButton = screen.queryByTestId(
      `${testIdBase}.remove`,
    ) as HTMLButtonElement;
    return { titleField, linkField, removeButton };
  };

  const assertDocumentationLinkFields = (
    value: { title: string; link: string },
    index: number,
  ) => {
    const { titleField, linkField } = getDocumentationLinkFields(index);
    expect(titleField.value).toEqual(value.title);
    expect(linkField.value).toEqual(value.link);
  };

  const fillDocumentationLinkFields = (
    value: { title: NimbusDocumentationLinkTitle; link: string },
    index: number,
  ) => {
    const { titleField, linkField } = getDocumentationLinkFields(index);
    fireEvent.change(titleField, {
      target: { value: value.title },
    });
    fireEvent.change(linkField, {
      target: { value: value.link },
    });
    fireEvent.blur(linkField);
  };

  const checkExistingForm = async (expected: Record<string, any>) => {
    for (const [labelText, fieldValue] of [
      ["Public name", expected.name],
      ["Hypothesis", expected.hypothesis],
      ["Public description", expected.publicDescription],
      ["Risk Mitigation Checklist Link", expected.riskMitigationLink],
      ["documentationLinks", expected.documentationLinks],
    ]) {
      if (labelText === "documentationLinks") {
        fieldValue.forEach(assertDocumentationLinkFields);
      } else {
        const fieldName = screen.getByLabelText(labelText) as HTMLInputElement;
        expect(fieldName.value).toEqual(fieldValue);
      }
    }
  };

  it("validates fields before allowing submit", async () => {
    const expected = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "DESKTOP",
    };

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);

    const submitButton = screen.getByTestId("submit-button");
    await act(async () => fillOutNewForm(expected));
    await act(async () => void fireEvent.click(submitButton));

    expect(onSubmit).toHaveBeenCalled();
    expect(onSubmit.mock.calls[0][0]).toEqual(expected);
  });

  it("requires a URL for the risk mitigation link", async () => {
    const { experiment } = mockExperimentQuery("boo");
    render(<Subject {...{ experiment }} />);
    const linkField = screen.getByTestId("riskMitigationLink");

    await act(async () => {
      fireEvent.change(linkField, {
        target: { value: "whatchu-talkin-bout-willis" },
      });
      fireEvent.blur(linkField);
    });

    expect(
      screen.getByTestId("FormOverview").querySelector(".invalid-feedback"),
    ).toHaveTextContent(FIELD_MESSAGES.URL);

    await act(async () => {
      fireEvent.change(linkField, {
        target: { value: "https://www.com" },
      });
      fireEvent.blur(linkField);
    });

    expect(
      screen.getByTestId("FormOverview").querySelector(".invalid-feedback"),
    ).toBeNull();
  });

  it("with existing experiment, checks fields and allows saving data", async () => {
    const { experiment } = mockExperimentQuery("boo");
    const onSubmit = jest.fn();
    const expected = {
      name: experiment.name,
      hypothesis: experiment.hypothesis as string,
      publicDescription: experiment.publicDescription as string,
      riskMitigationLink: experiment.riskMitigationLink as string,
      documentationLinks: experiment.documentationLinks as Record<string, any>,
    };

    render(<Subject {...{ onSubmit, experiment }} />);
    const saveButton = screen.getByTestId("submit-button");
    const nextButton = screen.getByTestId("next-button");
    const nameField = screen.getByLabelText("Public name");

    checkExistingForm(expected);

    fireEvent.change(nameField, { target: { value: "" } });
    fireEvent.blur(nameField);

    // Update the name in the form and expected data
    expected.name = "Let's Get Sentimental";
    fireEvent.change(nameField, {
      target: { value: expected.name },
    });
    fireEvent.blur(nameField);

    await act(async () => {
      fireEvent.click(saveButton);
      fireEvent.click(nextButton);
    });
    expect(onSubmit).toHaveBeenCalledTimes(2);
    expect(onSubmit.mock.calls).toEqual([
      // Save button just saves
      [expected, false],
      // Next button advances to next page
      [expected, true],
    ]);
  });

  it("with missing public description, still allows submit", async () => {
    const { experiment } = mockExperimentQuery("boo");

    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment }} />);
    const descriptionField = screen.getByLabelText("Public description");
    const submitButton = screen.getByTestId("submit-button");

    await act(async () => {
      fireEvent.change(descriptionField, { target: { value: "" } });
      fireEvent.blur(descriptionField);
    });

    expect(submitButton).toBeEnabled();

    await act(async () => void fireEvent.click(submitButton));
    expect(onSubmit).toHaveBeenCalled();
  });

  it("correctly renders, updates, filters, and deletes documentation links", async () => {
    const { experiment } = mockExperimentQuery("boo", {
      documentationLinks: [
        {
          __typename: "NimbusDocumentationLinkType",
          title: NimbusDocumentationLinkTitle.DS_JIRA,
          link: "https://bingo.bongo",
        },
      ],
    });

    const onSubmit = jest.fn();
    render(<Subject {...{ experiment, onSubmit }} />);
    const submitButton = screen.getByTestId("submit-button");
    const addButton = screen.getByText("+ Add Link");

    // Assert that the initial documentation link sets are rendered
    experiment.documentationLinks!.map(assertDocumentationLinkFields);

    // The first remove button should not be present
    expect(getDocumentationLinkFields(0).removeButton).toBeNull();

    // Update the values of the first set
    await act(async () => {
      experiment.documentationLinks![0] = {
        __typename: "NimbusDocumentationLinkType",
        title: NimbusDocumentationLinkTitle.ENG_TICKET,
        link: "https://",
      };
      fillDocumentationLinkFields(experiment.documentationLinks![0], 0);
    });

    // Whoops! Invalid URL.
    expect(
      screen
        .getByTestId("DocumentationLink")
        .querySelector(".invalid-feedback"),
    ).toHaveTextContent(FIELD_MESSAGES.URL);

    // Fix the invalid URL
    experiment.documentationLinks![0].link = "https://ooga.booga";
    await act(async () => {
      fillDocumentationLinkFields(experiment.documentationLinks![0], 0);
    });

    // Add a new set and populate it
    await act(async () => void fireEvent.click(addButton));
    await act(async () => {
      experiment.documentationLinks!.push({
        __typename: "NimbusDocumentationLinkType",
        title: NimbusDocumentationLinkTitle.DESIGN_DOC,
        link: "https://boingo.oingo",
      });
      fillDocumentationLinkFields(experiment.documentationLinks![1], 1);
    });

    // Add a new set and PARTIALLY populate it
    // This set should be filtered out and therefore will
    // not be added to expected output
    await act(async () => void fireEvent.click(addButton));
    await act(async () =>
      fillDocumentationLinkFields(
        {
          title: NimbusDocumentationLinkTitle.DESIGN_DOC,
          link: "",
        },
        2,
      ),
    );

    // Add a new set, and populate it with the data from the second field
    await act(async () => void fireEvent.click(addButton));
    await act(async () => {
      fillDocumentationLinkFields(experiment.documentationLinks![1], 3);
    });

    // Now delete the second set
    await act(
      async () =>
        void fireEvent.click(getDocumentationLinkFields(1).removeButton),
    );

    expect(screen.queryAllByTestId("DocumentationLink").length).toEqual(
      // Add one because this array doesn't include the field that will be filtered out
      experiment.documentationLinks!.length + 1,
    );

    await act(async () => void fireEvent.click(submitButton));

    expect(onSubmit.mock.calls[0][0].documentationLinks).toEqual(
      experiment.documentationLinks!.map(({ title, link }) => ({
        title,
        link,
      })),
    );
  });

  it("disables create submission when loading", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, isLoading: true }} />);

    // Fill out valid form to ensure only isLoading prevents submission
    await act(
      async () =>
        void fillOutNewForm({
          name: "Foo bar baz",
          hypothesis: "Some thing",
          application: "DESKTOP",
        }),
    );

    const submitButton = screen.getByTestId("submit-button");
    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent("Submitting");

    await act(async () => {
      fireEvent.click(submitButton);
      fireEvent.submit(screen.getByTestId("FormOverview"));
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("displays saving button when loading", async () => {
    const { experiment } = mockExperimentQuery("boo");
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit, experiment, isLoading: true }} />);

    const submitButton = screen.getByTestId("submit-button");
    waitFor(() => {
      expect(submitButton).toHaveTextContent("Saving");
    });
  });

  it("displays an alert for overall submit error", async () => {
    const submitErrors = {
      "*": ["Big bad happened"],
    };
    render(<Subject {...{ submitErrors }} />);
    await act(async () =>
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        submitErrors["*"][0],
      ),
    );
  });

  it("displays feedback for per-field error", async () => {
    const submitErrors = {
      name: ["That name is terrible, man"],
    };
    render(<Subject {...{ submitErrors }} />);
    const errorFeedback = screen.getByText(submitErrors["name"][0]);
    await act(async () => {
      expect(errorFeedback).toHaveClass("invalid-feedback");
      expect(errorFeedback).toHaveAttribute("data-for", "name");
    });
  });

  it("displays warning icon when public description is not filled out and server requires it", async () => {
    Object.defineProperty(window, "location", {
      value: {
        search: "?show-errors",
      },
    });

    const { experiment } = mockExperimentQuery("boo");
    const isMissingField = jest.fn(() => true);
    render(<Subject {...{ isMissingField, experiment }} />);

    waitFor(() => {
      expect(isMissingField).toHaveBeenCalled();
      expect(screen.queryByTestId("missing-description")).toBeInTheDocument();
    });
  });
});
