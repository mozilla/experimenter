window.showRecommendation = function () {
  const defaultControls = document.getElementById("default-controls");
  const recommendationMessage = document.getElementById(
    "recommendation-message",
  );
  defaultControls.classList.add("d-none");
  recommendationMessage.classList.remove("d-none");
};
window.toggleSubmitButton = function () {
  const checkbox1 = document.getElementById("checkbox-1");
  const checkbox2 = document.getElementById("checkbox-2");
  const submitButton = document.getElementById("request-launch-button");
  submitButton.disabled = !(checkbox1.checked && checkbox2.checked);
};

window.updatePreviewURL = function () {
  const select = document.getElementById("branch-selector");
  const previewUrl = document.getElementById("preview-url");
  const slugElement = document.getElementById("experiment-slug");

  if (select && previewUrl && slugElement) {
    const selectedSlug = select.value;
    const experimentSlug = slugElement.textContent.trim();
    const url = `about:studies?optin_slug=${experimentSlug}&optin_branch=${selectedSlug}&optin_collection=nimbus-preview`;
    previewUrl.textContent = url;
  }
};

function initializeRejectApproveListeners() {
  const rejectButton = document.getElementById("reject-button");
  const reviewControls = document.getElementById("review-controls");
  const rejectFormContainer = document.getElementById("reject-form-container");
  const cancelButton = document.getElementById("cancel");

  if (rejectButton) {
    rejectButton.addEventListener("click", () => {
      reviewControls.classList.add("d-none");
      rejectFormContainer.classList.remove("d-none");
    });
  }

  if (cancelButton) {
    cancelButton.addEventListener("click", () => {
      rejectFormContainer.classList.add("d-none");
      reviewControls.classList.remove("d-none");
    });
  }
}

// Initialize listeners on initial load
document.addEventListener("DOMContentLoaded", initializeRejectApproveListeners);

// Reinitialize listeners after HTMX content swaps
document.body.addEventListener("htmx:afterSwap", () => {
  initializeRejectApproveListeners();
});

document.body.addEventListener("htmx:beforeRequest", (event) => {
  const launchControls = document.getElementById("launch-controls");
  const overlay = launchControls?.querySelector("#htmx-loading-overlay");
  if (overlay && event.target.closest("#launch-controls")) {
    overlay.style.display = "flex";
  }
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  const launchControls = document.getElementById("launch-controls");
  const overlay = launchControls?.querySelector("#htmx-loading-overlay");
  if (overlay && event.target.closest("#launch-controls")) {
    overlay.style.display = "none";
  }
});
