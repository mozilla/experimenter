import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-select/dist/css/bootstrap-select.min.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "../css/style.scss";

import * as $ from "jquery";
import * as bootstrap from "bootstrap";
import "htmx.org";
import "bootstrap-select";

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
  const toastElList = document.querySelectorAll(".toast");
  [...toastElList].map((toastEl) => {
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
  });
};

$(() => {
  setupThemeSwitcher();
  setupTooltips();
  setupToasts();

  document.body.addEventListener("htmx:afterSwap", function () {
    $(".selectpicker").selectpicker();
    setupTooltips();
    setupToasts();
  });
});
