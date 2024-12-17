export default function toggleSubmitButton() {
  const checkboxes = document.querySelectorAll(".form-check-input");
  const submitButton = document.getElementById("request-launch-button");
  const allChecked = Array.from(checkboxes).every(
    (checkbox) => checkbox.checked,
  );
  submitButton.disabled = !allChecked;
}
document.body.addEventListener("htmx:afterSwap", () => {
  document.querySelectorAll(".form-check-input").forEach((checkbox) => {
    checkbox.addEventListener("change", toggleSubmitButton);
  });
});
