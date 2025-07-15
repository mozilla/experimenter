import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import { autocompletion } from "@codemirror/autocomplete";
import { schemaAutocomplete, schemaLinter } from "./validator.js";
import $ from "jquery";

const setupCodemirror = () => {
  const textareas = document.querySelectorAll(".value-editor");

  textareas.forEach((textarea) => {
    const jsonSchema = JSON.parse(textarea.dataset["schema"]);

    const extensions = [
      basicSetup,
      EditorView.updateListener.of((v) => {
        if (v.docChanged) {
          const value = v.state.doc.toString();
          const textarea = v.view.dom.parentNode.querySelector(".value-editor");
          textarea.value = value;
        }
      }),
      json(),
      linter(jsonParseLinter()),
      linter(schemaLinter(jsonSchema)),
      autocompletion({ override: [schemaAutocomplete(jsonSchema)] }),
    ];

    const view = new EditorView({
      doc: textarea.value || "{}",
      extensions,
      parent: textarea.parentNode,
    });

    view.dom.style.border = "1px solid #ccc";

    textarea.parentNode.insertBefore(view.dom, textarea);

    return view;
  });
};

$(() => {
  setupCodemirror();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCodemirror();
  });
});
