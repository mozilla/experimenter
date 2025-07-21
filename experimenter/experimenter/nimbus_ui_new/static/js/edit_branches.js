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
    doc: textarea.value || "{}",
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
    if (textarea.dataset.cmInitialized === "true") return;

    const jsonSchema = JSON.parse(textarea.dataset["schema"]);

    setupCodemirror(selector, textarea, [
      linter(schemaLinter(jsonSchema)),
      autocompletion({ override: [schemaAutocomplete(jsonSchema)] }),
    ]);

    textarea.dataset.cmInitialized = "true";
  });
};

const setupCodemirrorLabs = () => {
  const selector = "#id_firefox_labs_description_links";
  const textarea = document.querySelector(selector);

  if (!textarea || textarea.dataset.cmInitialized === "true") return;

  setupCodemirror(selector, textarea, []);
  textarea.dataset.cmInitialized = "true";
};

$(() => {
  setupCodemirrorFeatures();
  setupCodemirrorLabs();

  document.body.addEventListener("htmx:beforeSwap", function (event) {
    if (event.target.id === "branches-form") {
      document.querySelectorAll(".cm-editor").forEach((cm) => cm.remove());
      document.querySelectorAll(".value-editor").forEach((ta) => {
        delete ta.dataset.cmInitialized;
      });
    }
  });

  document.body.addEventListener("htmx:afterSwap", function () {
    setupCodemirrorFeatures();
    setupCodemirrorLabs();
  });
});
