jQuery(function ($) {
  function updateTechnicalRisk() {
    // Show/hide the technical risk description field.

    // From the Django point of view, the description is optional. But we make it
    // mandatory when the technical risk radio is checked.
    const hasTechnicalRisk = $('[type="radio"][name="risk_technical"][value="True"]:checked').length > 0;

    // We hide the confusing "Optional" label manually here (#888)
    $('#risks_technical_description_field .text-muted').hide();

    if (hasTechnicalRisk) {
      $('#risks_technical_description_field').show();
    } else {
      $('#risks_technical_description_field').hide();
    }
  }

  function updateRisks() {
    if ($('[type="radio"][value="True"]:checked').length > 0) {
      $('#risks_field').show();
    } else {
      $('#risks_field').hide();
    }
  }

  $('[type="radio"]').change(function (e) {
    updateRisks();
    updateTechnicalRisk();
  });

  updateRisks();
  updateTechnicalRisk();
});
