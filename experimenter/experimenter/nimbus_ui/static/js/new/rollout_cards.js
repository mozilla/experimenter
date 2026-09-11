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

document.addEventListener("keydown", (event) => {
  if (
    event.key === "Enter" &&
    event.target.closest?.(".card-edit-form input")
  ) {
    event.preventDefault();
  }
});

document.addEventListener("click", (event) => {
  const trigger = event.target.closest?.("[data-toast-id]");
  if (trigger) {
    showToast(trigger.dataset.toastId);
  }
});

const expandCard = (card) => {
  const collapse = card.querySelector(".accordion-collapse");
  if (collapse && !collapse.classList.contains("show")) {
    window.bootstrap?.Collapse.getOrCreateInstance(collapse, {
      toggle: false,
    }).show();
  }
};

document.addEventListener("click", (event) => {
  const editButton = event.target.closest?.("[data-card-action='edit']");
  const card = editButton?.closest(".rollout-card");
  if (card) {
    expandCard(card);
  }
});

const restoreCardFocus = (card) => {
  if (document.activeElement !== document.body) {
    return;
  }
  const form = card.querySelector(".card-edit-form");
  form?.setAttribute("tabindex", "-1");
  const target = form ?? card.querySelector("[data-card-action='edit']");
  target?.focus({ preventScroll: true });
};

let pendingCardId = null;

document.addEventListener("htmx:beforeRequest", (event) => {
  const element = event.detail.elt;
  const card = element.closest?.(".rollout-card");
  const swapsCard = element
    .getAttribute?.("hx-target")
    ?.startsWith("#rollout-");
  pendingCardId = card && swapsCard ? card.id : null;
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
    restoreCardFocus(card);
  }
});

document.addEventListener("DOMContentLoaded", syncCardEditActions);
