import { Compartment } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";

export const themeCompartment = new Compartment();

export const isDarkMode = () => {
  return document.documentElement.getAttribute("data-bs-theme") === "dark";
};

export const getThemeExtensions = () => (isDarkMode() ? [oneDark] : []);

const viewRegistry = new Set();

export const registerView = (view) => {
  viewRegistry.add(view);
};

export const updateViewTheme = (view) => {
  view.dispatch({
    effects: themeCompartment.reconfigure(getThemeExtensions()),
  });
};

export const updateAllViewThemes = () => {
  viewRegistry.forEach(updateViewTheme);
};

export const observeThemeChanges = (callback) => {
  new MutationObserver(() => callback()).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-bs-theme"],
  });
};
