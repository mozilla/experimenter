// Hook up cloning experiments
jQuery(function($) {
  let sendUrl;

  const modal = $("#clone-experiment-modal");
  const errorField = modal.find(".error-field");

  $("button.clone-experiment").on("click", function(e) {
    // make sure no previous error messages are showing
    errorField.addClass("d-none");
    errorField.text("");
    sendUrl = this.dataset.url;
    // Let Bootstrap handle showing the modal itself
  });


  modal.find("button.send").on("click", async function(e) {
    data = {"name": modal.find("#experiment-name-input").val()}

    this.innerHTML = "Cloning...";
    this.disabled = true;
    const resp = await fetch(sendUrl, {
      method: "PATCH",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    body = await resp.json();
    if (resp.status == 200) {
      location.replace(body.clone_url);
    } else {
      errorField.text(body.name[0])
      errorField.removeClass("d-none")
      this.disabled = false;
      this.innerHTML = "Clone";
    }
  });
});
