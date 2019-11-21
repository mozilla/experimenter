jQuery(function ($) {
  const rolloutType = "rollout";

  function updateDSOwner() {
    const group = $("#id_analysis_owner").closest('.form-group');
    if ($('#id_type option:selected').val() === rolloutType) {
      group.hide();
    } else {
      group.show();
    }
  }

  function updateDSBug() {
    const input = $("#id_data_science_bugzilla_url");
    const group = input.closest('.form-group');
    const label = $("label[for='id_data_science_bugzilla_url'] .required-label");
    if ($('#id_type option:selected').val() === rolloutType) {
      input.removeAttr("required");
      label.addClass("optional").removeClass("required");
      group.hide();
    } else {
      input.attr("required", "true");
      label.addClass("required").removeClass("optional");
      group.show();
    }
  }

  $('#id_type').change(function (e) {
    updateDSBug();
    updateDSOwner();
  });

  updateDSBug();
  updateDSOwner();
});
