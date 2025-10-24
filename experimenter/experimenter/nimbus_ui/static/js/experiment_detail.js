const setupCollapseRecipe = () => {
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
};

const setupPreviewUrlCopyToast = () => {
  var previewUrl = document.getElementById("preview-url");
  var copiedToast = document.getElementById("preview-toast");
  if (previewUrl && copiedToast) {
    previewUrl.addEventListener("click", function () {
      navigator.clipboard.writeText(previewUrl.textContent.trim());
      var toast = window.bootstrap.Toast.getOrCreateInstance(copiedToast);
      toast.show();
    });
  }
};

document.addEventListener("DOMContentLoaded", function () {
  setupCollapseRecipe();
  setupPreviewUrlCopyToast();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCollapseRecipe();
    setupPreviewUrlCopyToast();
  });
});
