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

const setupCodemirroReadOnlyJSON = () => {
  const selector = ".readonly-json";
  const textareas = document.querySelectorAll(selector);

  const highlightStyle = HighlightStyle.define([
    { tag: tags.bool, color: "#ffaa00ff", themeType: "dark" },
  ]);

  textareas.forEach((textarea) => {
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

    textarea.parentNode.insertBefore(view.dom, textarea);
    textarea.style.display = "none";

    return view;
  });
};

$(() => {
  setupCodemirroReadOnlyJSON();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCodemirroReadOnlyJSON();
  });
});
