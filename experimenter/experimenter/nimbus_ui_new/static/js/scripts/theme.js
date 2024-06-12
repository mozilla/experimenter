(() => {
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
})();
