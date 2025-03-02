document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("show_errors")) {
    const formIds = ["audience-form", "metrics-form"];

    formIds.forEach(function (formId) {
      const form = document.getElementById(formId);
      if (form) {
        form.requestSubmit();
      }
    });
  }
});
