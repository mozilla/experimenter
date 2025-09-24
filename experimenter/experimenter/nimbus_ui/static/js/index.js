import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-select/dist/css/bootstrap-select.min.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "../css/style.scss";

import * as $ from "jquery";
import * as bootstrap from "bootstrap";
import "htmx.org";
import "bootstrap-select";

window.bootstrap = bootstrap;
const setupThemeSwitcher = () => {
  const LIGHT = "light";
  const DARK = "dark";
  const getStoredTheme = () => localStorage.getItem("theme");
  const setStoredTheme = (theme) => localStorage.setItem("theme", theme);

  const getPreferredTheme = () => {
    const storedTheme = getStoredTheme();

    if (storedTheme) {
      return storedTheme;
    }

    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? DARK
      : LIGHT;
  };

  const setTheme = (theme) => {
    const themeSwitcher = document.querySelector("#theme-selector");
    themeSwitcher.checked = theme === LIGHT;
    document.documentElement.setAttribute("data-bs-theme", theme);
    setStoredTheme(theme);
  };

  setTheme(getPreferredTheme());

  const themeSwitcher = document.querySelector("#theme-selector");
  themeSwitcher.addEventListener("change", function () {
    const theme = themeSwitcher.checked ? LIGHT : DARK;
    setTheme(theme);
  });
};

const setupTooltips = () => {
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]',
  );
  [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );
};

const setupToasts = () => {
  const toastElList = document.querySelectorAll(".toast:not(.hide)");
  [...toastElList].map((toastEl) => {
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
  });
};

const setupSlugCopyToast = () => {
  var slug = document.getElementById("experiment-slug");
  var copiedToast = document.getElementById("slug-toast");
  if (slug && copiedToast) {
    slug.addEventListener("click", function () {
      navigator.clipboard.writeText(slug.textContent.trim());
      var toast = bootstrap.Toast.getOrCreateInstance(copiedToast);
      toast.show();
    });
  }
};

const setupHTMXLoadingOverlay = () => {
  document.addEventListener("htmx:beforeRequest", function () {
    const loadingOverlay = document.querySelector("#htmx-loading-overlay");
    if (loadingOverlay) {
      loadingOverlay.style.opacity = "0.75";
      loadingOverlay.style.pointerEvents = "auto";
    }
  });

  document.addEventListener("htmx:afterRequest", function () {
    const loadingOverlay = document.querySelector("#htmx-loading-overlay");
    if (loadingOverlay) {
      loadingOverlay.style.opacity = "0";
      loadingOverlay.style.pointerEvents = "none";
    }
  });
};

$(() => {
  setupThemeSwitcher();
  setupTooltips();
  setupToasts();
  setupSlugCopyToast();
  setupHTMXLoadingOverlay();

  document.body.addEventListener("htmx:afterSwap", function () {
    $(".selectpicker").selectpicker();
    setupTooltips();
    setupToasts();
    setupSlugCopyToast();
  });

  // To support HTMX onchange updates on selectpicker, we need to
  // bubble changes on selectpicker to the original select element
  // which will trigger the HTMX submit
  let isInternalChange = false;
  $(".selectpicker").on("changed.bs.select", function () {
    if (isInternalChange) {
      return;
    }
    isInternalChange = true;
    this.dispatchEvent(new Event("change", { bubbles: true }));
    isInternalChange = false;
  });
});
