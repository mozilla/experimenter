import { Compartment } from "@codemirror/state";
import { oneDark } from "@codemirror/theme-one-dark";

export const themeCompartment = new Compartment();

export const isDarkMode = () => {
  return document.documentElement.getAttribute("data-bs-theme") === "dark";
};

export const getThemeExtensions = () => (isDarkMode() ? [oneDark] : []);

const viewRegistry = new Set();

export const registerView = (view) => {
  viewRegistry.add(new WeakRef(view));
};

export const updateViewTheme = (view) => {
  view.dispatch({
    effects: themeCompartment.reconfigure(getThemeExtensions()),
  });
};

export const updateAllViewThemes = () => {
  const toRemove = [];

  for (const ref of viewRegistry) {
    const view = ref.deref();

    if (typeof view === "undefined") {
      toRemove.push(ref);
      continue;
    }

    updateViewTheme(view);
  }

  for (const ref of toRemove) {
    viewRegistry.delete(ref);
  }
};

export const observeThemeChanges = (callback) => {
  new MutationObserver(() => callback()).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-bs-theme"],
  });
};
