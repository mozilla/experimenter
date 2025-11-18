document.body.addEventListener("htmx:beforeRequest", function () {
  const spinner = document.querySelector("#htmx-table-spinner");
  if (spinner) {
    spinner.style.opacity = "1";
  }
});

document.body.addEventListener("htmx:afterRequest", function () {
  const spinner = document.querySelector("#htmx-table-spinner");
  if (spinner) {
    spinner.style.opacity = "0";
  }
});

document.body.addEventListener("htmx:afterSwap", function () {
  // After reloading the table, we must update the values for status and sort in the sidebar form
  // since it will not have been reloaded in the htmx get call
  const urlParams = new URLSearchParams(window.location.search);
  const sortValue = urlParams.get("sort");
  const statusValue = urlParams.get("status");
  document
    .querySelectorAll('#filter-form input[name="status"]')
    .forEach((e) => (e.value = statusValue));
  document
    .querySelectorAll('#filter-form input[name="sort"]')
    .forEach((e) => (e.value = sortValue));
});
