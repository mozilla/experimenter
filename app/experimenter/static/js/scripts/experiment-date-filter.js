let dateRangeSelector = document.getElementById('id_experiment_date_field');
let rangeElementInput0 = document.getElementById("id_date_range_0");
let rangeElementGroup = rangeElementInput0.closest(".form-group");

function setUpDateRange () {
  if (dateRangeSelector.value == '') {
    rangeElementGroup.setAttribute("hidden", "");
  } else {
    rangeElementGroup.removeAttribute("hidden");
  }
}

setUpDateRange();


dateRangeSelector.addEventListener("change", setUpDateRange);
