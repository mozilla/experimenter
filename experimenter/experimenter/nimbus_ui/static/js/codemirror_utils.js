import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import {
  themeCompartment,
  getThemeExtensions,
  registerView,
} from "./theme_utils.js";
import $ from "jquery";

const VISIBLE_LINE_COUNT = 5;

export const createReadonlyJsonEditor = (textarea) => {
  if (!textarea || textarea.dataset.is_rendered) return null;

  textarea.dataset.is_rendered = true;

  const extensions = [
    basicSetup,
    json(),
    linter(jsonParseLinter()),
    EditorState.readOnly.of(true),
    EditorView.editable.of(false),
    EditorView.lineWrapping,
    themeCompartment.of(getThemeExtensions()),
  ];

  const view = new EditorView({
    doc: textarea.value,
    extensions,
    parent: textarea.parentNode,
  });

  view.dom.style.border = "1px solid #ccc";
  view.dom.style.maxHeight = "inherit";
  textarea.parentNode.insertBefore(view.dom, textarea);
  textarea.style.display = "none";

  registerView(view);

  return view;
};

export const setupCodemirrorCollapsibleDisplay = (textarea) => {
  const lines = textarea.value.split("\n").length;

  if (lines > VISIBLE_LINE_COUNT) {
    textarea.parentNode.nextElementSibling?.classList.remove("d-none");
    textarea.nextElementSibling?.classList.remove("d-none");

    $(".show-btn").on("click", (e) => {
      e.target.parentNode.classList.add("d-none");
      e.target.parentNode.nextElementSibling.classList.remove("d-none");
    });

    $(".hide-btn").on("click", (e) => {
      e.target.parentNode.classList.add("d-none");
      e.target.parentNode.previousElementSibling.classList.remove("d-none");
    });
  }
};

export const setupReadonlyJsonEditors = () => {
  const textareas = document.querySelectorAll(".readonly-json");
  textareas.forEach((textarea) => {
    const view = createReadonlyJsonEditor(textarea);
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
