import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";

import $ from "jquery";

const setupCodemirroReadOnlyJSON = () => {
  const selector = ".readonly-json";
  const textareas = document.querySelectorAll(selector);

  textareas.forEach((textarea) => {
    if (textarea._codemirrorInitialized) {
      return;
    }
    textarea._codemirrorInitialized = true;
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

    textarea.parentNode.insertBefore(view.dom, textarea);
    textarea.style.display = "none";

    return view;
  });
};

$(() => {
  setupCodemirroReadOnlyJSON();
});
