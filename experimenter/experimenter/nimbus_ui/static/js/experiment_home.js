document.body.addEventListener("htmx:beforeRequest", function () {
  document.querySelectorAll(".htmx-spinner").forEach((spinner) => {
    spinner.style.opacity = "1";
  });
});

document.body.addEventListener("htmx:afterRequest", function () {
  document.querySelectorAll(".htmx-spinner").forEach((spinner) => {
    spinner.style.opacity = "0";
  });
});
