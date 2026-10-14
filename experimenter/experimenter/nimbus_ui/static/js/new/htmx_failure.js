const showRequestFailedToast = () => {
  const toastEl = document.getElementById("toast-request-failed");
  if (toastEl) {
    window.bootstrap?.Toast.getOrCreateInstance(toastEl).show();
  }
};

document.addEventListener("htmx:responseError", showRequestFailedToast);
document.addEventListener("htmx:sendError", showRequestFailedToast);
document.addEventListener("htmx:timeout", showRequestFailedToast);
