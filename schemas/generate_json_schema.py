"""
Heavily inspired by pydantic-to-typescript2 (itself a fork of pydantic-to-typescript):
https://github.com/Darius-Labs/pydantic-to-typescript2/blob/main/pydantic2ts/cli/script.py
"""

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import click
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, create_model

from mozilla_nimbus_schemas import experiments, jetstream


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
        "/* Do not modify by hand - update the pydantic models and re-run the script\n",
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

    if "enum" in schema and schema.get("description") == "An enumeration.":
        del schema["description"]

    # this prevents json2ts from adding `[k: string]: unknown;` to every interface
    if not schema.get("additionalProperties"):
        schema["additionalProperties"] = False


def iterate_models() -> dict[str, Any]:
    model_names = list(experiments.__all__) + list(jetstream.__all__)
    models = []
    for model_name_str in model_names:
        if model_name_str in experiments.__all__:
            model = getattr(experiments, model_name_str)
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


@click.command()
@click.option(
    "--output",
    "ts_output_path",
    type=Path,
    default=Path("index.d.ts"),
    help="Output typescript file.",
)
def main(*, ts_output_path: Path):
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


if __name__ == "__main__":
    main()
