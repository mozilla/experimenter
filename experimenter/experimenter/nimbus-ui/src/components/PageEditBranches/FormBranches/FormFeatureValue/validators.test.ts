import { json } from "@codemirror/lang-json";
import { EditorState, EditorStateConfig } from "@codemirror/state";
import { basicSetup } from "codemirror";
import {
  detectDraft,
  fmlLinter,
  schemaAutocomplete,
  schemaLinter,
  simpleObjectSchema,
} from "src/components/PageEditBranches/FormBranches/FormFeatureValue/validators";
import { z } from "zod";

const SIMPLE_SCHEMA: z.infer<typeof simpleObjectSchema> = {
  type: "object",
  properties: {
    foo: { type: "string" },
    bar: { type: "integer" },
    baz: { type: "boolean" },
  },
};

const COMPLEX_SCHEMA = {
  type: "object",
  properties: {
    foo: {
      type: "array",
      items: {
        type: "object",
        properties: {
          bar: {
            type: "string",
          },
        },
      },
    },
  },
};

function createEditorState(config: Partial<EditorStateConfig>): EditorState {
  return EditorState.create({
    extensions: [basicSetup, json()],
    ...config,
  });
}

describe("schemaLinter", () => {
  describe("simple schemas", () => {
    const linter = schemaLinter(SIMPLE_SCHEMA);

    it.each(["", "   ", "\t", "\n", " \n \t "])(
      "does not return errors for an empty document",
      (doc) => {
        const state = createEditorState({ doc });
        const diagnostics = linter({ state });

        expect(diagnostics).toEqual([]);
      },
    );

    it.each([
      ["{", "Unexpected end of input"],
      ["}", "Unexpected token <}> at 1:1"],
      ["[", "Unexpected end of input"],
      ["]", "Unexpected token <]> at 1:1"],
      ["asdf", "Unexpected symbol <a> at 1:1"],
      [",", "Unexpected token <,> at 1:1"],
    ])("returns errors about invalid JSON", (doc, message) => {
      const state = createEditorState({ doc });
      const diagnostics = linter({ state });

      expect(diagnostics).toEqual([expect.objectContaining({ message })]);
    });

    it.each([
      ["hello", "Expected a JSON Object, not string"],
      [1, "Expected a JSON Object, not number"],
      [true, "Expected a JSON Object, not boolean"],
      [[], "Expected a JSON Object, not Array"],
      [null, "Expected a JSON Object, not null"],
    ])("returns errors about non-object JSON", (doc, message) => {
      const state = createEditorState({ doc: JSON.stringify(doc) });
      const diagnostics = linter({ state });

      expect(diagnostics).toEqual([expect.objectContaining({ message })]);
    });

    it.each([
      [{ foo: 123 }, `Instance type "number" is invalid. Expected "string".`],
      [{ foo: true }, `Instance type "boolean" is invalid. Expected "string".`],
      [{ foo: {} }, `Instance type "object" is invalid. Expected "string".`],
      [{ foo: [] }, `Instance type "array" is invalid. Expected "string".`],
      [{ foo: null }, `Instance type "null" is invalid. Expected "string".`],
    ])("returns errors mismatched types", (doc, message) => {
      const state = createEditorState({ doc: JSON.stringify(doc) });
      const diagnostics = linter({ state });
      expect(diagnostics).toEqual([expect.objectContaining({ message })]);
    });

    it.each([{ x: { y: 123.456 } }, { x: [123.456] }, { x: [{ y: 123.456 }] }])(
      "returns errors about floating point values",
      (doc) => {
        const state = createEditorState({ doc: JSON.stringify(doc) });
        const diagnostics = linter({ state });
        expect(diagnostics).toEqual([
          expect.objectContaining({ message: "Floats are not supported" }),
        ]);
      },
    );
  });

  describe("additionalProperties", () => {
    it("errors reported", () => {
      const linter = schemaLinter({
        type: "object",
        additionalProperties: false,
      });
      const state = createEditorState({ doc: JSON.stringify({ foo: 123 }) });
      const diagnostics = linter({ state });

      expect(diagnostics).toEqual([
        expect.objectContaining({ message: `Unexpected property "foo"` }),
      ]);
    });

    it("does not report 'unexpected property' errors for mismatched types", () => {
      const linter = schemaLinter({
        type: "object",
        properties: {
          foo: { type: "string" },
        },
        additionalProperties: false,
      });
      const state = createEditorState({ doc: JSON.stringify({ foo: 123 }) });
      const diagnostics = linter({ state });

      expect(diagnostics).not.toContainEqual(
        expect.objectContaining({ message: `Unexpected property "foo"` }),
      );
      expect(diagnostics).toContainEqual(
        expect.objectContaining({
          message: `Instance type "number" is invalid. Expected "string".`,
        }),
      );
    });
  });

  it("required errors", () => {
    const linter = schemaLinter({
      type: "object",
      properties: {
        foo: { type: "string" },
      },
      required: ["foo"],
    });
    const state = createEditorState({ doc: JSON.stringify({}) });
    const diagnostics = linter({ state });
    expect(diagnostics).toEqual([
      expect.objectContaining({
        message: `Instance does not have required property "foo".`,
      }),
    ]);
  });

  it.each([
    [
      { foo: [{ bar: 123 }] },
      `Instance type "number" is invalid. Expected "string".`,
    ],
  ])("reports errors at arbitrary depths", (doc, message) => {
    const linter = schemaLinter(COMPLEX_SCHEMA);
    const state = createEditorState({ doc: JSON.stringify(doc) });
    const diagnostics = linter({ state });
    expect(diagnostics).toEqual([expect.objectContaining({ message })]);
  });

  it.each([
    [
      {
        type: "object",
        properties: {
          foo: { $ref: "#/$defs/foo" },
        },
        $defs: {
          foo: {
            const: "foo",
          },
        },
      },
      { foo: "bar" },
      "A subschema had errors",
    ],
    [
      {
        type: "object",
        if: {
          properties: {
            foo: { const: "foo" },
          },
        },
        then: {
          properties: {
            bar: { const: "bar" },
          },
          required: ["bar"],
        },
      },
      { foo: "foo" },
      `Instance does not match "then" schema.`,
    ],
    [
      {
        type: "object",
        if: {
          properties: {
            foo: { const: "foo" },
          },
        },
        else: {
          properties: {
            bar: { const: "bar" },
          },
          required: ["bar"],
        },
      },
      {
        foo: "bar",
      },
      `Instance does not match "else" schema.`,
    ],
    [
      {
        type: "object",
        allOf: [
          {
            properties: { foo: { const: "foo" } },
            required: ["foo"],
          },
          {
            properties: { bar: { const: "bar" } },
            required: ["bar"],
          },
        ],
      },
      {},
      "Instance does not match every subschema.",
    ],
    [
      {
        type: "object",
        properties: {
          foo: {
            type: "array",
            items: {
              type: "string",
            },
          },
        },
      },
      { foo: [1] },
      "Items did not match schema.",
    ],
  ])("Ignored repeated errors", (schema, doc, message) => {
    const linter = schemaLinter(schema);
    const state = createEditorState({ doc: JSON.stringify(doc) });
    const diagnostics = linter({ state });
    expect(diagnostics).not.toContainEqual(
      expect.objectContaining({ message }),
    );
  });
});

describe("schemaAutocomplete", () => {
  it("suggests all top-level variable names", () => {
    const state = createEditorState({ doc: `{""}` });
    const ctx = { state, pos: 2 };

    const autocomplete = schemaAutocomplete(SIMPLE_SCHEMA);
    expect(autocomplete).not.toBeNull();

    const result = autocomplete!(ctx);
    expect(result).toEqual(
      expect.objectContaining({
        options: [{ label: "foo" }, { label: "bar" }, { label: "baz" }],
      }),
    );
  });

  it("only suggests at top-level property names", () => {
    const state = createEditorState({ doc: `{"foo": {""}` });
    const ctx = { state, pos: 10 };

    const autocomplete = schemaAutocomplete(SIMPLE_SCHEMA);
    expect(autocomplete).not.toBeNull();

    const result = autocomplete!(ctx);
    expect(result).toEqual(null);
  });

  it("does not provide suggestions for complex schemas", () => {
    const autocomplete = schemaAutocomplete({
      allOf: [
        { type: "object", properties: { foo: { type: "string" } } },
        { type: "object", properties: { bar: { type: "string" } } },
      ],
    });

    expect(autocomplete).toBeNull();
  });
});

describe("detectDraft", () => {
  it.each([
    ["http://json-schema.org/draft-04/schema#", "4"],
    ["http://json-schema.org/draft-07/schema#", "7"],
    ["https://json-schema.org/draft/2019-09/schema", "2019-09"],
    ["https://json-schema.org/draft/2020-12/schema", "2020-12"],
    ["junk", "2019-09"],
    [undefined, "2019-09"],
  ])(
    "detects versions correctly",
    ($schema: string | undefined, expected: string) => {
      const schema: Record<string, unknown> = {};
      if (typeof $schema !== "undefined") {
        schema["$schema"] = $schema;
      }

      const detected = detectDraft(schema);

      expect(detected).toEqual(expected);
    },
  );
});

describe("fmlLinter", () => {
  it.each(["", "   ", "\t", "\n", " \n \t "])(
    "does not return fml errors for an empty document",
    (doc) => {
      const linter = fmlLinter();
      const state = createEditorState({ doc: JSON.stringify(doc) });
      const diagnostics = linter({ state });
      expect(diagnostics).toEqual([]);
    },
  );

  it.each([`{"foo": {"error"}`, `{"error": {"bingo"}`])(
    "returns FML errors",
    (doc) => {
      const linter = fmlLinter();
      const message = { message: "oh no!" };
      const state = createEditorState({ doc: JSON.stringify(doc) });
      const diagnostics = linter({ state });
      expect(diagnostics).toContainEqual(expect.objectContaining(message));
    },
  );

  it.each([`{"foo": {"bar"}`, `{"foo": {"mimsy"}`])(
    "does not returns FML errors",
    (doc) => {
      const linter = fmlLinter();
      const message = { message: "oh no!" };
      const state = createEditorState({ doc: JSON.stringify(doc) });
      const diagnostics = linter({ state });
      expect(diagnostics).not.toContainEqual(expect.objectContaining(message));
    },
  );
});
