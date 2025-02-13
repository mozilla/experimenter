document.addEventListener("DOMContentLoaded", function () {
  const collapseRecipe = document.getElementById("collapse-recipe");
  if (!collapseRecipe) return;

  const bsCollapse = new window.bootstrap.Collapse(collapseRecipe, {
    toggle: false,
  });

  function showRecipeJson() {
    bsCollapse.show();
  }
  // Expand JSON if URL contains the hash on page load
  if (window.location.hash.includes("preview-recipe-json")) {
    showRecipeJson();
  }
  // Ensure it expands every time "Preview Recipe JSON" is clicked
  const previewJsonLink = document.querySelector(
    'a[href$="preview-recipe-json"]',
  );
  if (previewJsonLink) {
    previewJsonLink.addEventListener("click", function () {
      setTimeout(showRecipeJson, 50);
    });
  }
});
