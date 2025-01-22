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

function initializeRejectApproveListeners() {
  const rejectButton = document.getElementById("reject-button");
  const reviewControls = document.getElementById("review-controls");
  const rejectFormContainer = document.getElementById("reject-form-container");
  const cancelReject = document.getElementById("cancel-reject");

  if (rejectButton) {
    rejectButton.addEventListener("click", () => {
      reviewControls.classList.add("d-none");
      rejectFormContainer.classList.remove("d-none");
    });
  }

  if (cancelReject) {
    cancelReject.addEventListener("click", () => {
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
