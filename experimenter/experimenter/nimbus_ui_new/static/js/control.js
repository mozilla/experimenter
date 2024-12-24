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
