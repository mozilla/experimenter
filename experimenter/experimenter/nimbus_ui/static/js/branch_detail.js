import { updateAllViewThemes, observeThemeChanges } from "./theme_utils.js";
import $ from "jquery";

$(() => {
  observeThemeChanges(updateAllViewThemes);
});
