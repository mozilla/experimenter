document.addEventListener("DOMContentLoaded", function () {
  const collapseRecipe = document.getElementById("collapse-recipe");
  if (!collapseRecipe) return;
  const bsCollapse = new window.bootstrap.Collapse(collapseRecipe, {
    toggle: false,
  });
  collapseRecipe.addEventListener("hide.bs.collapse", () => bsCollapse.hide());

  function showRecipeJson() {
    if (window.location.hash.includes("preview-recipe-json")) {
      bsCollapse.show();
    }
  }
  showRecipeJson();
  window.addEventListener("hashchange", showRecipeJson);
});
