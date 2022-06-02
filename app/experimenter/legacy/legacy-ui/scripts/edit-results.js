function updateResults() {
  const failureNotes =
    $('[type="radio"][name="results_recipe_errors"][value="True"]:checked')
      .length > 0;

  if (failureNotes) {
    $("#results-failure-notes").show();
  } else {
    $("#results-failure-notes").hide();
  }
}

$('[type="radio"]').change(function (e) {
  updateResults();
});

updateResults();
