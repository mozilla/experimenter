import * as $ from "jquery";

const setupRangeSlider = () => {
  const rangeInput = document.getElementById("id_population_percent_slider");
  const textInput = document.getElementById("id_population_percent");

  // Update text input when range slider changes
  rangeInput.addEventListener("input", function () {
    textInput.value = rangeInput.value;
  });

  // Update range slider when text input changes
  textInput.addEventListener("input", function () {
    rangeInput.value = textInput.value;
  });
};

$(() => {
  setupRangeSlider();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupRangeSlider();
  });
});
