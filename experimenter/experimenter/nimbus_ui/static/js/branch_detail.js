import {
  drawSelection,
  EditorView,
  highlightSpecialChars,
  lineNumbers,
} from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import {
  HighlightStyle,
  syntaxHighlighting,
  defaultHighlightStyle,
  foldGutter,
} from "@codemirror/language";
import { tags } from "@lezer/highlight";

import $ from "jquery";

const VISIBLE_LINE_COUNT = 5;

const setupCodemirroReadOnlyJSON = () => {
  const selector = ".readonly-json";
  const textareas = document.querySelectorAll(selector);

  const highlightStyle = HighlightStyle.define([
    { tag: tags.bool, color: "#ffaa00ff", themeType: "dark" },
  ]);

  textareas.forEach((textarea) => {
    if (textarea.dataset.is_rendered) return;
    textarea.dataset.is_rendered = true;
    const extensions = [
      lineNumbers(),
      drawSelection(),
      highlightSpecialChars(),
      foldGutter(),
      syntaxHighlighting(highlightStyle),
      syntaxHighlighting(defaultHighlightStyle),
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
    view.dom.style.maxHeight = "inherit";
    textarea.parentNode.insertBefore(view.dom, textarea);
    textarea.style.display = "none";

    setupCodemirrorCollapsibleDisplay(textarea);

    return view;
  });
};

const setupCodemirrorCollapsibleDisplay = (textarea) => {
  const lines = textarea.value.split("\n").length;

  if (lines > VISIBLE_LINE_COUNT) {
    // Removes d-none from both buttons for json views that can be collapsed
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

$(() => {
  setupCodemirroReadOnlyJSON();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCodemirroReadOnlyJSON();
  });
});
