import {
  getByText,
  getAllByText,
  waitFor,
  fireEvent,
  getByTestId,
} from "@testing-library/react";

export async function waitForFormToLoad(container) {
  await waitFor(() => getByText(container, "Save Draft"), { container });
}

export function addBranch(container) {
  fireEvent.click(getByText(container, "Add Branch"));
}

export function removeBranch(container, index) {
  fireEvent.click(getAllByText(container, "Remove Branch")[index]);
}

export function addPrefBranch(container, variantIndex) {
  fireEvent.click(getAllByText(container, "Add Pref")[variantIndex]);
}

export function removePrefBranch(container, variantIndex, prefIndex) {
  fireEvent.click(
    getByTestId(container, `remove-pref-${variantIndex}-${prefIndex}`),
  );
}
