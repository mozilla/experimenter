"""
Heavily inspired by pydantic-to-typescript2 (itself a fork of pydantic-to-typescript):
https://github.com/Darius-Labs/pydantic-to-typescript2/blob/main/pydantic2ts/cli/script.py
"""

import json
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable

import click
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, create_model

from mozilla_nimbus_schemas import experiments, experiments_v7, jetstream

NEWLINES_RE = re.compile("\n+")


def clean_output_file(ts_path: Path) -> None:
    """Clean up the output file typescript definitions were written to by:

    1. Removing the 'top model'.
       This is a faux pydantic model with references to all the *actual* models necessary
       for generating clean typescript definitions without any duplicates. We don't
       actually want it in the output, so this function removes it from the generated
       typescript file.
    2. Adding a banner comment with clear instructions for how to regenerate the
       typescript definitions.
    """
    with ts_path.open("r") as f:
        lines = f.readlines()

    start, end = None, None
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == "export interface _TopModel_ {":
            start = i
        elif (start is not None) and line.rstrip("\r\n") == "}":
            end = i
            break

    banner_comment_lines = [
        "/* tslint:disable */\n",
        "/* eslint-disable */\n",
        "/**\n",
        "/* This file was automatically generated from pydantic models.\n",
        "/* Do not modify by hand - update the pydantic models and re-run\n",
        " * make schemas_build\n",
        " */\n\n",
    ]

    new_lines = banner_comment_lines + lines[:start] + lines[(end + 1) :]

    with ts_path.open("w") as f:
        f.writelines(new_lines)


def clean_schema(schema: dict[str, Any]) -> None:
    """Clean up the resulting JSON schemas by:

    1. Removing titles from JSON schema properties.
       If we don't do this, each property will have its own interface in the
       resulting typescript file (which is a LOT of unnecessary noise).
    2. Getting rid of the useless "An enumeration." description applied to Enums
       which don't have a docstring.
    """
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
        if "$ref" in prop:
            # json-schema-to-typescript will generate a redundant type.
            prop.pop("description", None)

    if "enum" in schema and schema.get("description") == "An enumeration.":
        del schema["description"]

    # this prevents json2ts from adding `[k: string]: unknown;` to every interface
    if not schema.get("additionalProperties"):
        schema["additionalProperties"] = False


def iterate_models() -> dict[str, Any]:
    model_names = (
        list(experiments.__all__) + list(jetstream.__all__) + list(experiments_v7.__all__)
    )

    models = []
    for model_name_str in model_names:
        if model_name_str in experiments.__all__:
            model = getattr(experiments, model_name_str)
        elif model_name_str in experiments_v7.__all__:
            model = getattr(experiments_v7, model_name_str)
        else:
            model = getattr(jetstream, model_name_str)
        if not issubclass(model, ModelFactory):
            models.append(model)
    top_model: BaseModel = create_model(
        "_TopModel_", **{m.__name__: (m, ...) for m in models}
    )

    schema: dict = top_model.model_json_schema(mode="serialization")

    for d in schema.get("$defs", {}).values():
        clean_schema(d)

    return schema


def prettify_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    # Add a $schema field.
    pretty_schema = {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
    }

    # Re-order the properties in the dict so that they are in a sensible order
    # for humans consuming these schemas.

    # Use this order for top-level keys.
    key_order = [
        "title",
        "description",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "if",
        "then",
        "$defs",
    ]

    # If there are any other keys not listed above, splice them in before $defs.
    key_order = [
        *key_order[:-1],
        *(set(schema.keys()) - set(key_order)),
        key_order[-1],
    ]

    pretty_schema.update({key: schema[key] for key in key_order if key in schema})

    # Assert that the schemas have not structurally changed.
    #
    # We have to add the $schema field back to the original schema for comparison.
    schema["$schema"] = pretty_schema["$schema"]
    assert schema == pretty_schema

    # Next, lets walk the schema and remove attributes we don't care about.
    def _walk_objects(objs: Iterable[dict[str, Any]]):
        for obj in objs:
            _walk_object(obj)

    def _walk_object(obj: dict[str, Any], top_level: bool = False):
        # All but the top-level title will be auto-generated base on field names. They are
        # not useful.
        if not top_level:
            obj.pop("title", None)

        # We don't support defaults.
        obj.pop("default", None)

        # This is an OpenAPI extension and it leads to incorrect code generation in our
        # case (due to using a boolean discriminator).
        obj.pop("discriminator", None)

        # Strip newlines from descriptions.
        if description := obj.get("description"):
            obj["description"] = NEWLINES_RE.sub(" ", description)

        # Remove redundant enum entries for constants.
        if obj.get("const") is not None:
            obj.pop("enum", None)

        match obj.get("type"):
            case "object":
                if properties := obj.get("properties"):
                    _walk_objects(properties.values())

            case "array":
                if items := obj.get("items"):
                    _walk_object(items)

        for group_key in ("allOf", "anyOf", "oneOf"):
            if group := obj.get(group_key):
                _walk_objects(group)

    _walk_object(pretty_schema, top_level=True)
    if defs := pretty_schema.get("$defs"):
        _walk_objects(defs.values())

    return pretty_schema


def write_json_schemas(json_schemas_path: Path, python_package_dir: Path):
    json_schemas_path.mkdir(exist_ok=True)

    models = {
        model_name: getattr(experiments, model_name)
        for model_name in experiments.__all__
        if issubclass(getattr(experiments, model_name), BaseModel)
    }

    written_paths = set()

    for model_name, model in models.items():
        model_schema_path = json_schemas_path / f"{model_name}.schema.json"
        written_paths.add(model_schema_path)

        json_schema = prettify_json_schema(model.model_json_schema())
        with model_schema_path.open("w") as f:
            json.dump(json_schema, f, indent=2)
            f.write("\n")

    # Ensure we don't include any files in schemas/ that we did not generate (e.g., if a
    # model gets removed).
    for path in list(json_schemas_path.iterdir()):
        if path not in written_paths:
            path.unlink()

    # Copy schemas into the python package.
    schemas_dist_dir = python_package_dir / "schemas"
    if schemas_dist_dir.exists():
        shutil.rmtree(schemas_dist_dir)

    shutil.copytree(json_schemas_path, schemas_dist_dir)


@click.command()
@click.option(
    "--output",
    "ts_output_path",
    type=Path,
    default=Path("index.d.ts"),
    help="Output typescript file.",
)
@click.option(
    "--json-schemas",
    "json_schemas_path",
    type=Path,
    default=Path("schemas"),
    help="Output JSON Schemas to this directory.",
)
@click.option(
    "--python-package-dir",
    "python_package_dir",
    type=Path,
    default=Path("mozilla_nimbus_schemas"),
    help=(
        "The directory to the mozilla-nimbus-schemas python package.\n"
        "\n"
        "Schemas will be installed inside this package at the schemas dir."
    ),
)
def main(*, ts_output_path: Path, json_schemas_path: Path, python_package_dir: Path):
    json_schema = iterate_models()

    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        schema_file_path = tmp_dir / "schema.json"

        with schema_file_path.open("w") as f:
            json.dump(json_schema, f)

        subprocess.run(
            [
                "yarn",
                "json2ts",
                "-i",
                str(schema_file_path),
                "-o",
                str(ts_output_path),
                "--bannerComment",
                "",
            ],
            check=True,
        )

        clean_output_file(ts_output_path)

    write_json_schemas(json_schemas_path, python_package_dir)


if __name__ == "__main__":
    main()
