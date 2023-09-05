module.exports = {
  content: ["../../templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        spaceCadet: "#242D4Eff",
        lenurple: "#b590d4",
        darkSlateBlue: "#4C4893ff",
        rythm: "#7D68A7ff",
        azure: "#007bff"
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/line-clamp"),
    require("@tailwindcss/aspect-ratio"),
  ],
};
