import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { json } from "@codemirror/lang-json";
import {
  themeCompartment,
  getThemeExtensions,
  registerView,
} from "./theme_utils.js";
import $ from "jquery";

const VISIBLE_LINE_COUNT = 5;

export const createReadonlyJsonEditor = (textarea, maxLines = null) => {
  if (!textarea || textarea.dataset.is_rendered) return null;

  textarea.dataset.is_rendered = true;

  const lines = textarea.value.split("\n");
  const docContent =
    maxLines && lines.length > maxLines
      ? lines.slice(0, maxLines).join("\n")
      : textarea.value;

  const view = new EditorView({
    doc: docContent,
    extensions: [
      basicSetup,
      json(),
      EditorState.readOnly.of(true),
      EditorView.editable.of(false),
      EditorView.lineWrapping,
      themeCompartment.of(getThemeExtensions()),
    ],
    parent: textarea.parentNode,
  });

  view.dom.style.border = "1px solid #ccc";

  textarea.parentNode.insertBefore(view.dom, textarea);
  textarea.style.display = "none";

  registerView(view);
  return view;
};

export const setupCodemirrorCollapsibleDisplay = (textarea) => {
  if (textarea.value.split("\n").length <= VISIBLE_LINE_COUNT) return;

  const collapsedCell = textarea.closest(".collapsed-json");
  const expandedCell = collapsedCell?.nextElementSibling;
  if (!collapsedCell || !expandedCell) return;

  collapsedCell.querySelector(".show-btn")?.classList.remove("d-none");
  expandedCell.querySelector(".hide-btn")?.classList.remove("d-none");

  $(collapsedCell)
    .find(".show-btn")
    .on("click", () => {
      $(collapsedCell).addClass("d-none");
      $(expandedCell).removeClass("d-none");
    });

  $(expandedCell)
    .find(".hide-btn")
    .on("click", () => {
      $(expandedCell).addClass("d-none");
      $(collapsedCell).removeClass("d-none");
    });
};

export const setupReadonlyJsonEditors = () => {
  document.querySelectorAll(".readonly-json").forEach((textarea) => {
    const maxLines = textarea.closest(".collapsed-json")
      ? VISIBLE_LINE_COUNT
      : null;
    const view = createReadonlyJsonEditor(textarea, maxLines);

    if (view) {
      setupCodemirrorCollapsibleDisplay(textarea);
      setupCopyButton(textarea, view);
    }
  });
};

const setupCopyButton = (textarea, view) => {
  const copyButton = textarea.parentNode.querySelector(".codemirror-copy-btn");
  if (!copyButton) return;

  copyButton.addEventListener("click", () => {
    const content = view.state.doc.toString();
    navigator.clipboard.writeText(content).then(() => {
      const toast = document.getElementById("json-copy-toast");
      if (toast) {
        const bsToast = window.bootstrap.Toast.getOrCreateInstance(toast);
        bsToast.show();
      }
    });
  });
};
