document.body.addEventListener("htmx:beforeRequest", function () {
  const spinners = document.querySelectorAll(".htmx-spinner");
  spinners.forEach((spinner) => {
    spinner.style.opacity = "1";
  });
});

document.body.addEventListener("htmx:afterRequest", function () {
  const spinners = document.querySelectorAll(".htmx-spinner");
  spinners.forEach((spinner) => {
    spinner.style.opacity = "0";
  });
});
