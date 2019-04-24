let dateRangeSelector = document.getElementById('id_experiment_date_field');
let rangeElementInput0 = document.getElementById("id_date_range_0");
let rangeElementInput1 = document.getElementById("id_date_range_1");


function setUpDateRange () {
  if (dateRangeSelector.value == '') {
    rangeElementInput0.setAttribute("disabled", "")
    rangeElementInput1.setAttribute("disabled", "")
  } else {
    rangeElementInput0.removeAttribute("disabled");
    rangeElementInput1.removeAttribute("disabled");
  }
}

setUpDateRange();


dateRangeSelector.addEventListener("change", setUpDateRange);
