const disposeAllTooltips = () => {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    window.bootstrap?.Tooltip.getInstance(el)?.dispose();
  });
};

document.addEventListener("htmx:beforeSwap", disposeAllTooltips);
