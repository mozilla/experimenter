// Initialize the bootstrap-select plugin
// https://developer.snapappointments.com/bootstrap-select/
jQuery(function($) {
  $("select[multiple]")
    .selectpicker()
    .on("changed.bs.select", function(e, clickedIndex) {
      const $this = $(this);
      if (clickedIndex === 0) {
        // User selected 'All'
        $this.val("__all__");
        $this.selectpicker("refresh");
      } else {
        // User selected anything by 'All'
        if ($this.selectpicker("val").includes("__all__")) {
          $this.val(
            $this.selectpicker("val").filter(value => value !== "__all__")
          );
          $this.selectpicker("refresh");
        }
      }
    });
});
