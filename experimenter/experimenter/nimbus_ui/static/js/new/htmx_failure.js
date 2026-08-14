let reloadingAfterHtmxFailure = false;

const reloadOnHtmxFailure = () => {
  if (reloadingAfterHtmxFailure) {
    return;
  }
  reloadingAfterHtmxFailure = true;
  window.location.reload();
};

document.addEventListener("htmx:responseError", reloadOnHtmxFailure);
document.addEventListener("htmx:sendError", reloadOnHtmxFailure);
document.addEventListener("htmx:timeout", reloadOnHtmxFailure);
