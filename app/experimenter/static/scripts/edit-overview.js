jQuery(function ($) {
  const rolloutType = "rollout";

  function updateHiddenFields() {
    const fields = ["analysis_owner", "data_science_issue_url"];
    const requiredFields = ["data_science_issue_url"];

    for (const field of fields) {
      const input = $(`#id_${field}`);
      const group = input.closest(".form-group");
      const label = $(`label[for="id_${field}"] .required-label`);
      if ($("#id_type option:selected").val() === rolloutType) {
        group.hide();

        if (requiredFields.includes(field)) {
          input.removeAttr("required");
          label.addClass("optional").removeClass("required");
        }
      } else {
        group.show();

        if (requiredFields.includes(field)) {
          input.attr("required", "true");
          label.addClass("required").removeClass("optional");
        }
      }
    }
  }

  $("#id_type").change(function (e) {
    updateHiddenFields();
  });

  updateHiddenFields();
});
