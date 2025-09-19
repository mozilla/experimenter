import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";

import $ from "jquery";

const VISIBLE_LINE_COUNT = 5;

const setupCodemirroReadOnlyJSON = () => {
  const selector = ".readonly-json";
  const textareas = document.querySelectorAll(selector);

  textareas.forEach((textarea) => {
    if (textarea.dataset.is_rendered) return;
    textarea.dataset.is_rendered = true;
    const extensions = [
      basicSetup,
      json(),
      linter(jsonParseLinter()),
      EditorState.readOnly.of(true),
      EditorView.editable.of(false),
    ];

    const view = new EditorView({
      doc: textarea.value,
      extensions,
      parent: textarea.parentNode,
    });

    view.dom.style.border = "1px solid #ccc";
    view.dom.style.maxHeight = `${22.4 * VISIBLE_LINE_COUNT + 5}px`;
    view.dom.lastChild.style.overflowY = "hidden";
    textarea.parentNode.insertBefore(view.dom, textarea);
    textarea.style.display = "none";

    setupCodemirrorCollapsibleDisplay(textarea, view);

    return view;
  });
};

const setupCodemirrorCollapsibleDisplay = (textarea, view) => {
  const lines = textarea.value.split("\n").length;
  console.log(textarea, lines);

  if (lines > VISIBLE_LINE_COUNT) {
    const showHideButton = document.createElement("button");
    showHideButton.className = "btn btn-outline-primary btn-sm mt-2 d-block";
    showHideButton.innerHTML = '<i class="fa-solid fa-plus"></i> Show more';

    let isExpanded = false;

    showHideButton.addEventListener("click", () => {
      isExpanded = !isExpanded;
      showHideButton.innerHTML = isExpanded
        ? '<i class="fa-solid fa-minus"></i> Show less'
        : '<i class="fa-solid fa-plus"></i> Show more';
      view.dom.style.maxHeight = isExpanded
        ? "none"
        : `${22.4 * VISIBLE_LINE_COUNT + 5}px`;
    });

    textarea.parentNode.insertBefore(showHideButton, textarea);
  }
};

$(() => {
  setupCodemirroReadOnlyJSON();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCodemirroReadOnlyJSON();
  });
});
