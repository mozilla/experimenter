import { MergeView } from "@codemirror/merge";
import { EditorView, basicSetup } from "codemirror";
import { EditorState } from "@codemirror/state";
import { json } from "@codemirror/lang-json";

const setupMergeViews = () => {
  const containers = document.querySelectorAll(".schema-merge-container");

  containers.forEach((container) => {
    // Skip if already initialized
    if (container.classList.contains("cm-initialized")) {
      return;
    }

    const currentJson = container.dataset.current;
    const previousJson = container.dataset.previous;

    if (!currentJson || !previousJson) {
      console.warn("Missing schema data for container", container);
      return;
    }

    // Create merge view
    new MergeView({
      a: {
        doc: previousJson,
        extensions: [
          basicSetup,
          json(),
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ],
      },
      b: {
        doc: currentJson,
        extensions: [
          basicSetup,
          json(),
          EditorView.editable.of(false),
          EditorState.readOnly.of(true),
        ],
      },
      parent: container,
    });

    // Mark as initialized
    container.classList.add("cm-initialized");
  });
};

// Wait for DOM to be ready
document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("htmx:afterSwap", function () {
    setupMergeViews();
  });

  document.body.addEventListener("shown.bs.collapse", function () {
    setupMergeViews();
  });
});
