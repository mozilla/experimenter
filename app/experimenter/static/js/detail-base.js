// Hook up cloning experiments
jQuery(function($) {
  let sendUrl;
  $("button.clone-experiment").on("click", function(e) {
    sendUrl = this.dataset.url;
    // Let Bootstrap handle showing the modal itself
  });

  const modal = $("#clone-experiment-modal");

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
    if (resp.status == 200) {
      body = await resp.json();
      location.replace(body.clone_url);
    } else {
      modal.find(".name-error").removeClass("d-none");
      this.disabled = false;
      this.innerHTML = "Clone";
    }
  });
});
