from enum import Enum
import json

from pydantic import BaseModel

from mozilla_nimbus_schemas import experiments
from mozilla_nimbus_schemas import jetstream


def iterate_models():
    json_str = ""
    for model_str in experiments.__all__:
        model = getattr(experiments, model_str)
        # print(model, type(model))

        if issubclass(model, BaseModel):
            model_str = json.dumps(model.model_json_schema())
            # print(model_str)
        elif issubclass(model, Enum):
            # TODO: handle Enums (and any other non-BaseModel types)
            # model_str = json.dumps([model])
            pass
            # print(model)
        json_str += model_str
        json_str += "\n"

    for model_str in jetstream.__all__:
        model = getattr(jetstream, model_str)
        # print(model, type(model))

        if issubclass(model, BaseModel):
            model_str = json.dumps(model.model_json_schema())
            # print(model_str)
        elif issubclass(model, Enum):
            # TODO: handle Enums (and any other non-BaseModel types)
            # model_str = json.dumps([model])
            pass
            # print(model)
        json_str += model_str
        json_str += "\n"

    return json_str


if __name__ == "__main__":
    print(iterate_models())
