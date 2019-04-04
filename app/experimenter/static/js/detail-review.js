// Hook up intent-to-ship email
jQuery(function($) {
  let sendUrl;
  $("button.send-intent-to-ship").on("click", function(e) {
    sendUrl = this.dataset.url;
    // Let Bootstrap handle showing the modal itself
  });

  const modal = $("#send-intent-to-ship-modal");

  modal.find("button.send").on("click", async function(e) {
    this.innerHTML = "Sending...";
    this.disabled = true;
    const resp = await fetch(sendUrl, {
      method: "PUT",
    });
    if (resp.status == 200) {
      modal.modal("hide");
      // Update the checkbox to match our out-of-band knowledge of
      // what happened.
      $("#id_review_intent_to_ship").prop("checked", true);
    } else {
      modal.find(".sending-failed").toggleClass("d-none");
    }
  });
});
