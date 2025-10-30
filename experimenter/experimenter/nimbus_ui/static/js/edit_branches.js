import {
  drawSelection,
  EditorView,
  highlightActiveLine,
  highlightSpecialChars,
  keymap,
  lineNumbers,
} from "@codemirror/view";
import { json, jsonParseLinter } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import { autocompletion, closeBrackets } from "@codemirror/autocomplete";
import {
  HighlightStyle,
  syntaxHighlighting,
  defaultHighlightStyle,
  foldGutter,
  bracketMatching,
  indentOnInput,
} from "@codemirror/language";
import {
  highlightSelectionMatches,
  searchKeymap,
  search,
} from "@codemirror/search";
import { defaultKeymap, historyKeymap, history } from "@codemirror/commands";
import { tags } from "@lezer/highlight";
import { schemaAutocomplete, schemaLinter, fmlLinter } from "./validator.js";
import $ from "jquery";

const setupCodemirror = (selector, textarea, extraExtensions) => {
  if (!textarea) {
    console.warn(`No textarea found for selector: ${selector}`);
    return;
  }

  const highlightStyle = HighlightStyle.define([
    { tag: tags.bool, color: "#ffaa00ff", themeType: "dark" },
  ]);

  const extensions = [
    lineNumbers(),
    drawSelection(),
    highlightSpecialChars(),
    foldGutter(),
    autocompletion(),
    bracketMatching(),
    closeBrackets(),
    highlightSelectionMatches(),
    indentOnInput(),
    highlightActiveLine(),
    syntaxHighlighting(highlightStyle),
    syntaxHighlighting(defaultHighlightStyle),
    history(),
    search(),
    keymap.of([...defaultKeymap, ...searchKeymap, ...historyKeymap]),
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
