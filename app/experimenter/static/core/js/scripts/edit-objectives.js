function updateSurvey() {
  const survey_required = $('[type="radio"][name="survey_required"][value="True"]:checked').length > 0;

  if (survey_required) {
    $('#survey-url-and-instructions').show()
  } else {
    $('#survey-url-and-instructions').hide();
  }
}

$('[type="radio"]').change(function (e) {
  updateSurvey();

});

updateSurvey();
