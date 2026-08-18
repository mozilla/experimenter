const showToast = (toastId) => {
  const toastEl = document.getElementById(toastId);
  if (toastEl) {
    window.bootstrap?.Toast.getOrCreateInstance(toastEl).show();
  }
};

const syncCardEditActions = () => {
  document.querySelectorAll(".rollout-card").forEach((card) => {
    const editing = card.querySelector(".card-edit-form") !== null;
    card
      .querySelectorAll("[data-card-action='edit']")
      .forEach((button) => button.classList.toggle("d-none", editing));
    card
      .querySelectorAll("[data-card-action='cancel']")
      .forEach((button) => button.classList.toggle("d-none", !editing));
  });
};

document.addEventListener("showToast", (event) => {
  showToast(event.detail?.id);
});

document.addEventListener("click", (event) => {
  const trigger = event.target.closest?.("[data-toast-id]");
  if (trigger) {
    showToast(trigger.dataset.toastId);
  }
});

let pendingCardId = null;

document.addEventListener("htmx:beforeRequest", (event) => {
  const card = event.detail.elt.closest?.(".rollout-card");
  pendingCardId = card ? card.id : null;
});

document.addEventListener("htmx:afterSwap", syncCardEditActions);

document.addEventListener("htmx:afterSettle", () => {
  const cardId = pendingCardId;
  pendingCardId = null;
  if (!cardId) {
    return;
  }
  const card = document.getElementById(cardId);
  if (card) {
    card.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
});

document.addEventListener("DOMContentLoaded", syncCardEditActions);
