$(() => {
  document.body.addEventListener("htmx:afterSwap", function () {
    $(".selectpicker").selectpicker();
  });
});
