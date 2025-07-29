import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import { autocompletion } from "@codemirror/autocomplete";
import { schemaAutocomplete, schemaLinter } from "./validator.js";
import $ from "jquery";

const setupCodemirror = (selector, textarea, extraExtensions) => {
  if (!textarea) {
    console.warn(`No textarea found for selector: ${selector}`);
    return;
  }

  const extensions = [
    basicSetup,
    EditorView.updateListener.of((v) => {
      if (v.docChanged) {
        const value = v.state.doc.toString();
        const textarea = v.view.dom.parentNode.querySelector(selector);
        textarea.value = value;
      }
    }),
    json(),
    linter(jsonParseLinter()),
    ...extraExtensions,
  ];

  const view = new EditorView({
    doc: textarea.value,
    extensions,
    parent: textarea.parentNode,
  });

  view.dom.style.border = "1px solid #ccc";

  textarea.parentNode.insertBefore(view.dom, textarea);

  return view;
};

const setupCodemirrorFeatures = () => {
  const selector = ".value-editor";
  const textareas = document.querySelectorAll(selector);

  textareas.forEach((textarea) => {
    const jsonSchema = JSON.parse(textarea.dataset["schema"]);

    setupCodemirror(selector, textarea, [
      linter(schemaLinter(jsonSchema)),
      autocompletion({ override: [schemaAutocomplete(jsonSchema)] }),
    ]);
  });
};

const setupCodemirrorLabs = () => {
  const selector = "#id_firefox_labs_description_links";
  const textarea = document.querySelector(selector);

  setupCodemirror(selector, textarea, []);
};

const setupCodeMirrorLocalizations = () => {
  const selector = "#id_localizations";
  const textarea = document.querySelector(selector);

  setupCodemirror(selector, textarea, []);
};

$(() => {
  setupCodemirrorFeatures();
  setupCodemirrorLabs();
  setupCodeMirrorLocalizations();

  document.body.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target.id === "branches-form") {
      setupCodemirrorFeatures();
      setupCodemirrorLabs();
      setupCodeMirrorLocalizations();
    }
  });
});
