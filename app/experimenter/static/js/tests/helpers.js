import { getByText, waitForElement, fireEvent } from "@testing-library/react";

export async function waitForFormToLoad(container) {
  await waitForElement(() => getByText(container, "Save Draft"), { container });
}

export function addBranch(container) {
  fireEvent.click(getByText(container, "Add Branch"));
}

export function removeBranch(container) {
  fireEvent.click(getByText(container, "Remove Branch"));
}
