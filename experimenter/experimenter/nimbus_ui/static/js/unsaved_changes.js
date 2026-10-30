const FORM_SELECTOR = "form[data-warn-unsaved]";
const IGNORED_FIELDS = new Set(["csrfmiddlewaretoken", "save_action"]);

// lastModified is excluded: on an empty file input it is the moment the
// FormData was built, so including it makes every serialization differ.
const describeValue = (value) =>
  value instanceof File ? `${value.name}:${value.size}` : value;

const serialize = (form) =>
  [...new FormData(form).entries()]
    .filter(([name]) => !IGNORED_FIELDS.has(name))
    .map(([name, value]) => `${name}=${describeValue(value)}`)
    .join("&");

// Keyed on the element, not the id: a save swaps in a freshly rendered form,
// and that new node gets a new baseline while an unsaved one keeps its own.
const baselines = new WeakMap();

// Save and Continue returns HX-Redirect with no body, so the edited form is
// still on the page when the browser navigates.
let allowUnload = false;

const watchedForms = () => [...document.querySelectorAll(FORM_SELECTOR)];

const baselineNewForms = () => {
  watchedForms().forEach((form) => {
    if (!baselines.has(form)) {
      baselines.set(form, serialize(form));
    }
  });
};

const hasUnsavedChanges = () =>
  watchedForms().some(
    (form) => baselines.has(form) && baselines.get(form) !== serialize(form),
  );

export const setupUnsavedChangesWarning = () => {
  baselineNewForms();

  document.body.addEventListener("htmx:afterSettle", baselineNewForms);

  document.body.addEventListener("htmx:beforeOnLoad", (event) => {
    if (event.detail.xhr?.getResponseHeader("HX-Redirect")) {
      allowUnload = true;
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (!allowUnload && hasUnsavedChanges()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
};
