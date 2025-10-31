import { basicSetup } from "codemirror";
import { EditorView } from "@codemirror/view";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import { autocompletion } from "@codemirror/autocomplete";
import { schemaAutocomplete, schemaLinter, fmlLinter } from "./validator.js";
import {
  themeCompartment,
  getThemeExtensions,
  registerView,
  updateAllViewThemes,
  observeThemeChanges,
} from "./theme_utils.js";
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
    themeCompartment.of(getThemeExtensions()),
    ...extraExtensions,
  ];

  const view = new EditorView({
    doc: textarea.value,
    extensions,
    parent: textarea.parentNode,
  });

  view.dom.style.border = "1px solid #ccc";

  textarea.parentNode.insertBefore(view.dom, textarea);
  textarea.style.display = "none";

  registerView(view);

  return view;
};

const setupCodemirrorFeatures = () => {
  const selector = ".value-editor";
  const textareas = document.querySelectorAll(selector);

  textareas.forEach((textarea) => {
    const extensions = [];

    const hasFmlValidation =
      textarea.dataset.experimentSlug && textarea.dataset.featureSlug;
    const hasJsonSchema = textarea.dataset.schema;

    if (hasFmlValidation) {
      extensions.push(
        linter(
          fmlLinter(
            textarea.dataset.experimentSlug,
            textarea.dataset.featureSlug,
          ),
        ),
      );

      if (hasJsonSchema) {
        const jsonSchema = JSON.parse(textarea.dataset.schema);
        extensions.push(
          autocompletion({ override: [schemaAutocomplete(jsonSchema)] }),
        );
      }
    } else if (hasJsonSchema) {
      const jsonSchema = JSON.parse(textarea.dataset.schema);

      extensions.push(
        linter(schemaLinter(jsonSchema)),
        autocompletion({ override: [schemaAutocomplete(jsonSchema)] }),
      );
    }

    setupCodemirror(selector, textarea, extensions);
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

const initializeAllEditors = () => {
  setupCodemirrorFeatures();
  setupCodemirrorLabs();
  setupCodeMirrorLocalizations();
};

$(() => {
  initializeAllEditors();
  observeThemeChanges(updateAllViewThemes);

  document.body.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target.id === "branches-form") {
      initializeAllEditors();
    }
  });
});
